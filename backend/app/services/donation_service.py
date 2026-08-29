"""
Donations via Stripe Checkout.

The money leaves the donor's account inside Stripe; this module's job is to
keep our record of it honest. Two things follow from that, and most of the
code here is one or the other:

**We are not the authority on what was paid.** ``DonationCreate.amount`` is a
number a browser sent us. The amount that was actually charged only exists in
the Checkout Session, and the only trustworthy way we learn it is a signed
webhook. So the webhook compares the two before it marks anything completed,
and a mismatch is a discrepancy to record and refuse, not a rounding error to
wave through.

**The webhook endpoint is unauthenticated.** Anything that reaches it came
from the open internet. Its signature check is the entire boundary, so it
fails closed: no configuration means no processing, never a fallback secret.
"""

from __future__ import annotations

import hmac
import logging
import os
import uuid
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.donation import Donation
from app.models.stripe_webhook_event import StripeWebhookEvent
from app.models.user import User
from app.schemas.donation import DonationCreate

try:  # pragma: no cover - exercised by the import-failure test via patching
    import stripe
except ImportError:  # pragma: no cover
    stripe = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# Currency the checkout session is created in. Kept as a module constant so
# the webhook has something to compare the session's currency against; Stripe
# reports it lowercased.
DONATION_CURRENCY = "usd"

# Stripe amounts are in the currency's minor unit. A donation below 50 cents
# is rejected by Stripe itself, and there is no reason to write a row that we
# know cannot become a payment.
MIN_DONATION_CENTS = 50
MAX_DONATION_CENTS = 1_000_000  # $10,000


class StripeNotConfigured(RuntimeError):
    """
    Stripe is unusable: the package is missing, or a required secret is not
    set.

    Separate from ``ValueError`` because it is an operator problem, not a
    caller problem, and the router turns it into a 503 rather than a 400.
    """


class WebhookVerificationError(ValueError):
    """The request did not come from Stripe, or did not survive parsing."""


class PaymentDiscrepancy(ValueError):
    """
    A verified event does not describe the payment we recorded.

    Reaching this means Stripe told us about a session whose amount, currency
    or status disagrees with the ``Donation`` row it points at. That is worth
    an alert rather than a silent completion.
    """


def _require_stripe():
    """Return the ``stripe`` module, or explain why there isn't one."""
    if stripe is None:
        raise StripeNotConfigured(
            "The 'stripe' package is not installed; donation endpoints are "
            "unavailable."
        )
    return stripe


def _require_env(name: str) -> str:
    """
    Read a required Stripe secret.

    No default. The previous version of this module fell back to
    ``"sk_test_mock_key"`` and ``"whsec_mock_secret"``, both of which are in
    the repository. For the API key that meant checkout appeared configured
    and silently was not; for the webhook secret it meant signature
    verification passed for anyone who read this file. An unset secret has to
    be a loud failure, because a quiet one is indistinguishable from working.
    """
    value = os.getenv(name)
    if not value or not value.strip():
        raise StripeNotConfigured(
            f"{name} is not set. Donations cannot be processed without it."
        )
    return value.strip()


def _signature_error_types() -> tuple[type[Exception], ...]:
    """
    The exception Stripe raises for a bad signature, across SDK versions.

    stripe-python moved the error classes from ``stripe.error`` to the top
    level in v8. Referencing only ``stripe.error`` raises ``AttributeError``
    on a new SDK, which reads as a 500 rather than the rejection it is.
    """
    candidates: list[type[Exception]] = []
    module = stripe
    if module is None:  # pragma: no cover - guarded by callers
        return (ValueError,)

    top_level = getattr(module, "SignatureVerificationError", None)
    if isinstance(top_level, type) and issubclass(top_level, Exception):
        candidates.append(top_level)

    legacy_ns = getattr(module, "error", None)
    legacy = getattr(legacy_ns, "SignatureVerificationError", None)
    if (
        isinstance(legacy, type)
        and issubclass(legacy, Exception)
        and legacy not in candidates
    ):
        candidates.append(legacy)

    return tuple(candidates) or (ValueError,)


def _coerce_donation_id(raw: Any) -> Optional[uuid.UUID]:
    """
    Parse ``client_reference_id`` into a UUID, or return ``None``.

    This value is echoed back by Stripe but it originates in a webhook body,
    and on the failure paths below we have not yet established that the body
    is one we wrote. Passing a non-UUID string into a query against a UUID
    column raises a driver-level ``DataError``, which surfaces as a 500. A
    value that is not a UUID is simply not one of our donations.
    """
    if raw is None:
        return None
    if isinstance(raw, uuid.UUID):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        return uuid.UUID(raw)
    except (ValueError, AttributeError, TypeError):
        return None


def _session_field(session: Any, key: str, default: Any = None) -> Any:
    """
    Read a field from a Stripe session object.

    Stripe's objects are dict-like, but tests and older SDK versions hand
    back plain dicts, so go through ``.get`` when it exists and fall back to
    attribute access.
    """
    if hasattr(session, "get"):
        try:
            return session.get(key, default)
        except TypeError:  # pragma: no cover - defensive
            pass
    return getattr(session, key, default)


class DonationService:
    # ------------------------------------------------------------------ #
    #  Checkout                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_checkout_session(
        db: Session, donation_data: DonationCreate, donor_id: uuid.UUID | None
    ) -> str:
        """
        Create a Stripe Checkout Session and the pending ``Donation`` it
        will complete.

        The row is written before the session exists because the session
        needs the row's id as its ``client_reference_id`` -- that is the
        thread the webhook follows back. If Stripe then rejects the session
        the row is marked ``failed`` rather than left dangling as ``pending``,
        so "pending" keeps meaning "we are waiting on Stripe" rather than
        "something went wrong here once".
        """
        client = _require_stripe()
        api_key = _require_env("STRIPE_SECRET_KEY")
        client.api_key = api_key

        recipient = db.query(User).filter(User.id == donation_data.recipient_id).first()
        if not recipient:
            raise ValueError("Recipient not found")

        if donor_id is not None and donor_id == recipient.id:
            raise ValueError("You cannot donate to yourself")

        if not getattr(recipient, "is_active", True):
            raise ValueError("Recipient is not accepting donations")

        donation = Donation(
            donor_id=donor_id,
            recipient_id=donation_data.recipient_id,
            amount=donation_data.amount,
            currency=DONATION_CURRENCY,
            status="pending",
            message=donation_data.message,
        )
        db.add(donation)
        db.commit()
        db.refresh(donation)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        recipient_name = " ".join(
            part
            for part in (recipient.first_name, recipient.last_name)
            if part
        ) or recipient.username

        try:
            session = client.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": DONATION_CURRENCY,
                            "product_data": {
                                "name": f"Donation to {recipient_name}",
                                "description": donation_data.message
                                or "Thank you for your support!",
                            },
                            "unit_amount": donation_data.amount,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=(
                    f"{frontend_url}/profile/{recipient.username}?donation=success"
                ),
                cancel_url=(
                    f"{frontend_url}/profile/{recipient.username}?donation=cancelled"
                ),
                client_reference_id=str(donation.id),
            )
        except Exception as exc:
            donation.status = "failed"
            db.commit()
            logger.warning(
                "Stripe checkout session creation failed for donation %s: %s",
                donation.id,
                exc,
            )
            raise RuntimeError("Failed to create Stripe checkout session") from exc

        donation.stripe_session_id = _session_field(session, "id")
        db.commit()

        url = _session_field(session, "url")
        if not url:
            donation.status = "failed"
            db.commit()
            raise RuntimeError("Stripe returned a checkout session with no URL")

        return url

    # ------------------------------------------------------------------ #
    #  Webhook                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def handle_webhook(db: Session, payload: bytes, sig_header: str) -> str:
        """
        Verify and dispatch one Stripe webhook delivery.

        Returns a short outcome string for the response body, which is useful
        in the Stripe dashboard's delivery log when working out whether an
        event was handled or deliberately skipped.

        Raises ``WebhookVerificationError`` for anything that fails the
        signature check -- the caller turns that into a 400 so Stripe stops
        retrying a request we will never accept.
        """
        client = _require_stripe()
        webhook_secret = _require_env("STRIPE_WEBHOOK_SECRET")

        try:
            event = client.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as exc:
            raise WebhookVerificationError("Invalid payload") from exc
        except _signature_error_types() as exc:
            raise WebhookVerificationError("Invalid signature") from exc

        event_id = _session_field(event, "id")
        event_type = _session_field(event, "type")

        if not event_id or not event_type:
            raise WebhookVerificationError("Event is missing an id or type")

        # Claim the event id before doing any work. A retry that arrives while
        # the first delivery is still in flight loses the insert here rather
        # than running the handler a second time.
        if not DonationService._claim_event(db, event_id, event_type):
            logger.info("Ignoring already-processed Stripe event %s", event_id)
            return "duplicate"

        data = _session_field(event, "data") or {}
        session = _session_field(data, "object") or {}

        if event_type == "checkout.session.completed":
            return DonationService._handle_checkout_completed(db, event_id, session)

        if event_type in (
            "checkout.session.async_payment_failed",
            "checkout.session.expired",
        ):
            return DonationService._handle_checkout_failed(db, session, event_type)

        logger.debug("Stripe event type %s needs no handling", event_type)
        return "ignored"

    # ------------------------------------------------------------------ #
    #  Webhook helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _claim_event(db: Session, event_id: str, event_type: str) -> bool:
        """
        Record ``event_id`` as being processed. ``False`` if it already was.

        The uniqueness is enforced by the primary key, not by a preceding
        SELECT, so two concurrent deliveries of the same event cannot both
        pass this check.
        """
        existing = (
            db.query(StripeWebhookEvent)
            .filter(StripeWebhookEvent.event_id == event_id)
            .first()
        )
        if existing is not None:
            return False

        db.add(StripeWebhookEvent(event_id=event_id, event_type=event_type))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return False
        return True

    @staticmethod
    def _handle_checkout_completed(db: Session, event_id: str, session: Any) -> str:
        """
        Mark a donation completed, if the session really describes it.

        Everything compared here is compared because Stripe is the only party
        that knows the answer and the ``Donation`` row is the only place we
        wrote our expectation down. If they disagree, the row is wrong, and
        completing it would be recording a payment that did not happen the way
        we think it did.
        """
        donation_id = _coerce_donation_id(_session_field(session, "client_reference_id"))
        if donation_id is None:
            logger.warning(
                "Stripe event %s has no usable client_reference_id", event_id
            )
            return "unmatched"

        donation = db.query(Donation).filter(Donation.id == donation_id).first()
        if donation is None:
            logger.warning(
                "Stripe event %s references unknown donation %s",
                event_id,
                donation_id,
            )
            return "unmatched"

        if donation.status == "completed":
            # A different event id for the same session -- for example a
            # replay after a manual resend from the dashboard.
            return "already_completed"

        DonationService._assert_session_matches(donation, session)

        payment_status = _session_field(session, "payment_status")
        if payment_status != "paid":
            logger.info(
                "Donation %s left pending: session payment_status is %r",
                donation.id,
                payment_status,
            )
            return "pending_payment"

        session_id = _session_field(session, "id")
        if session_id and not donation.stripe_session_id:
            donation.stripe_session_id = session_id

        donation.status = "completed"

        event_record = (
            db.query(StripeWebhookEvent)
            .filter(StripeWebhookEvent.event_id == event_id)
            .first()
        )
        if event_record is not None:
            event_record.donation_id = donation.id

        db.commit()

        DonationService._notify_recipient(db, donation)
        return "completed"

    @staticmethod
    def _assert_session_matches(donation: Donation, session: Any) -> None:
        """
        Check the charged amount and currency against what we recorded.

        ``amount_total`` is the number Stripe actually collected. Comparing it
        to ``donation.amount`` is the difference between recording a payment
        and recording a claim about one.
        """
        amount_total = _session_field(session, "amount_total")
        if amount_total is None:
            raise PaymentDiscrepancy(
                f"Session for donation {donation.id} reports no amount_total"
            )

        try:
            amount_total = int(amount_total)
        except (TypeError, ValueError) as exc:
            raise PaymentDiscrepancy(
                f"Session for donation {donation.id} has a non-numeric "
                f"amount_total: {amount_total!r}"
            ) from exc

        if amount_total != donation.amount:
            raise PaymentDiscrepancy(
                f"Donation {donation.id} recorded {donation.amount} but Stripe "
                f"collected {amount_total}"
            )

        currency = _session_field(session, "currency")
        if currency is not None:
            expected = (donation.currency or DONATION_CURRENCY).lower()
            # Constant-time only because it costs nothing here; the real
            # reason for the explicit compare is the case-folding.
            if not hmac.compare_digest(str(currency).lower(), expected):
                raise PaymentDiscrepancy(
                    f"Donation {donation.id} is in {expected} but Stripe "
                    f"collected {currency}"
                )

    @staticmethod
    def _handle_checkout_failed(db: Session, session: Any, event_type: str) -> str:
        """
        Move a donation out of ``pending`` when its session will not complete.

        ``async_payment_failed`` follows a ``checkout.session.completed`` for
        delayed payment methods, so a donation can arrive here after being
        marked completed. Reversing a completion is a refund question and not
        something to do implicitly, so that case is logged and left alone.
        """
        donation_id = _coerce_donation_id(_session_field(session, "client_reference_id"))
        if donation_id is None:
            return "unmatched"

        donation = db.query(Donation).filter(Donation.id == donation_id).first()
        if donation is None:
            return "unmatched"

        if donation.status == "completed":
            logger.warning(
                "Received %s for donation %s which is already completed; "
                "leaving it for manual review",
                event_type,
                donation.id,
            )
            return "needs_review"

        donation.status = "failed"
        db.commit()
        return "failed"

    @staticmethod
    def _notify_recipient(db: Session, donation: Donation) -> None:
        """
        Tell the recipient about a completed donation.

        Deliberately after the commit that completes the donation, and
        deliberately swallowing its own errors: a notification backend being
        down is not a reason to return a non-2xx and have Stripe redeliver an
        event we have already applied.
        """
        try:
            from app.models.notification import NotificationType
            from app.schemas.notification import NotificationCreate
            from app.services.notification_service import NotificationService

            amount = f"${donation.amount / 100:.2f}"
            notif = NotificationCreate(
                recipient_id=donation.recipient_id,
                type=NotificationType.MESSAGE,
                title="New Donation Received!",
                message=f"You received a donation of {amount}!",
                action_url="/donations",
            )
            NotificationService.create_notification(
                db=db,
                recipient_id=donation.recipient_id,
                sender_id=donation.donor_id,
                notification=notif,
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception(
                "Failed to notify recipient of completed donation %s", donation.id
            )
