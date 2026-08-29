"""
Tests for issue #1398: the donation webhook.

The webhook is the only unauthenticated write path in the donations feature,
so most of what is asserted here is about what it *refuses*: an event signed
with the wrong secret, an event that reports a different amount from the one
we recorded, an event we have already applied, an event that points at a
donation id which is not a UUID.

Stripe itself is not exercised. ``stripe.Webhook.construct_event`` is the
boundary, and these tests replace it with a stub that either returns an event
or raises the way the real one does, so the assertions are about our handling
rather than about the SDK's HMAC implementation.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.donation import Donation
from app.models.stripe_webhook_event import StripeWebhookEvent
from app.models.user import User
from app.schemas.donation import DonationCreate
from app.services import donation_service as ds
from app.services.donation_service import (
    DonationService,
    PaymentDiscrepancy,
    StripeNotConfigured,
    WebhookVerificationError,
)

pytestmark = pytest.mark.usefixtures("setup_db")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _make_user(db: Session, username: str) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        username=username,
        email=f"{username}@example.com",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_donation(
    db: Session,
    recipient: User,
    *,
    amount: int = 2500,
    status: str = "pending",
    donor: User | None = None,
) -> Donation:
    donation = Donation(
        donor_id=donor.id if donor else None,
        recipient_id=recipient.id,
        amount=amount,
        currency="usd",
        status=status,
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


def _event(
    event_type: str,
    session: dict,
    event_id: str = "evt_test_1",
) -> dict:
    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": session},
    }


def _session(
    donation_id,
    *,
    amount_total: int = 2500,
    currency: str = "usd",
    payment_status: str = "paid",
    session_id: str = "cs_test_1",
) -> dict:
    return {
        "id": session_id,
        "client_reference_id": str(donation_id) if donation_id else None,
        "amount_total": amount_total,
        "currency": currency,
        "payment_status": payment_status,
    }


class _StubStripe:
    """A stand-in for the ``stripe`` module, returning a canned event."""

    class SignatureVerificationError(Exception):
        pass

    def __init__(self, event=None, raises: Exception | None = None):
        self._event = event
        self._raises = raises
        self.api_key = None
        self.Webhook = SimpleNamespace(construct_event=self._construct_event)
        self.checkout = SimpleNamespace(Session=SimpleNamespace(create=MagicMock()))

    def _construct_event(self, payload, sig_header, secret):
        if self._raises is not None:
            raise self._raises
        return self._event


@pytest.fixture
def stripe_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_from_env")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_from_env")


# --------------------------------------------------------------------------
# Configuration must fail closed
# --------------------------------------------------------------------------


def test_missing_webhook_secret_is_refused_not_defaulted(db, monkeypatch):
    """
    The bug: the secret defaulted to ``whsec_mock_secret``, a value published
    in this repository, so an unset environment variable meant every forged
    request verified.
    """
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    stub = _StubStripe(event=_event("checkout.session.completed", _session(None)))

    with patch.object(ds, "stripe", stub):
        with pytest.raises(StripeNotConfigured):
            DonationService.handle_webhook(db, b"{}", "sig")


def test_blank_webhook_secret_is_treated_as_missing(db, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "   ")
    stub = _StubStripe(event=_event("checkout.session.completed", _session(None)))

    with patch.object(ds, "stripe", stub):
        with pytest.raises(StripeNotConfigured):
            DonationService.handle_webhook(db, b"{}", "sig")


def test_missing_api_key_is_refused_at_checkout(db, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    recipient = _make_user(db, "recipient_nokey")

    with patch.object(ds, "stripe", _StubStripe()):
        with pytest.raises(StripeNotConfigured):
            DonationService.create_checkout_session(
                db,
                DonationCreate(recipient_id=recipient.id, amount=2500),
                donor_id=None,
            )


def test_absent_stripe_package_raises_not_configured(db, stripe_env):
    """
    The module already guarded ``import stripe`` and set it to ``None``, then
    used it unguarded. Without the package every endpoint raised
    ``AttributeError: 'NoneType' object has no attribute 'checkout'``.
    """
    with patch.object(ds, "stripe", None):
        with pytest.raises(StripeNotConfigured):
            DonationService.handle_webhook(db, b"{}", "sig")


# --------------------------------------------------------------------------
# Signature verification
# --------------------------------------------------------------------------


def test_bad_signature_becomes_a_verification_error(db, stripe_env):
    stub = _StubStripe(raises=_StubStripe.SignatureVerificationError("nope"))

    with patch.object(ds, "stripe", stub):
        with pytest.raises(WebhookVerificationError):
            DonationService.handle_webhook(db, b"{}", "bad-sig")


def test_unparseable_payload_becomes_a_verification_error(db, stripe_env):
    stub = _StubStripe(raises=ValueError("not json"))

    with patch.object(ds, "stripe", stub):
        with pytest.raises(WebhookVerificationError):
            DonationService.handle_webhook(db, b"{", "sig")


def test_signature_error_class_is_found_on_the_legacy_namespace(db, stripe_env):
    """
    stripe-python moved the error classes to the top level in v8. The old code
    named only ``stripe.error.SignatureVerificationError``, which raises
    ``AttributeError`` on a new SDK -- turning a rejection into a 500.
    """

    class LegacyError(Exception):
        pass

    def _raise(payload, sig_header, secret):
        raise LegacyError("nope")

    # A stub with no top-level ``SignatureVerificationError`` at all, so the
    # only place the class can be found is the old namespace.
    stub = SimpleNamespace(
        api_key=None,
        Webhook=SimpleNamespace(construct_event=_raise),
        error=SimpleNamespace(SignatureVerificationError=LegacyError),
    )

    with patch.object(ds, "stripe", stub):
        with pytest.raises(WebhookVerificationError):
            DonationService.handle_webhook(db, b"{}", "sig")


# --------------------------------------------------------------------------
# The happy path
# --------------------------------------------------------------------------


def test_completed_session_marks_the_donation_completed(db, stripe_env):
    recipient = _make_user(db, "recipient_ok")
    donation = _make_donation(db, recipient, amount=2500)
    stub = _StubStripe(
        event=_event("checkout.session.completed", _session(donation.id, amount_total=2500))
    )

    with patch.object(ds, "stripe", stub):
        outcome = DonationService.handle_webhook(db, b"{}", "sig")

    assert outcome == "completed"
    db.refresh(donation)
    assert donation.status == "completed"


def test_completed_session_backfills_the_session_id(db, stripe_env):
    recipient = _make_user(db, "recipient_sid")
    donation = _make_donation(db, recipient)
    assert donation.stripe_session_id is None

    stub = _StubStripe(
        event=_event(
            "checkout.session.completed",
            _session(donation.id, session_id="cs_backfilled"),
        )
    )
    with patch.object(ds, "stripe", stub):
        DonationService.handle_webhook(db, b"{}", "sig")

    db.refresh(donation)
    assert donation.stripe_session_id == "cs_backfilled"


# --------------------------------------------------------------------------
# What was actually paid
# --------------------------------------------------------------------------


def test_amount_mismatch_is_refused(db, stripe_env):
    """
    The recorded amount comes from the browser; the charged amount comes from
    Stripe. Nothing compared them, so the two were independent numbers.
    """
    recipient = _make_user(db, "recipient_amount")
    donation = _make_donation(db, recipient, amount=5000)
    stub = _StubStripe(
        event=_event(
            "checkout.session.completed", _session(donation.id, amount_total=100)
        )
    )

    with patch.object(ds, "stripe", stub):
        with pytest.raises(PaymentDiscrepancy):
            DonationService.handle_webhook(db, b"{}", "sig")

    db.refresh(donation)
    assert donation.status == "pending"


def test_currency_mismatch_is_refused(db, stripe_env):
    recipient = _make_user(db, "recipient_currency")
    donation = _make_donation(db, recipient, amount=2500)
    stub = _StubStripe(
        event=_event(
            "checkout.session.completed",
            _session(donation.id, amount_total=2500, currency="eur"),
        )
    )

    with patch.object(ds, "stripe", stub):
        with pytest.raises(PaymentDiscrepancy):
            DonationService.handle_webhook(db, b"{}", "sig")

    db.refresh(donation)
    assert donation.status == "pending"


def test_currency_comparison_is_case_insensitive(db, stripe_env):
    recipient = _make_user(db, "recipient_case")
    donation = _make_donation(db, recipient, amount=2500)
    stub = _StubStripe(
        event=_event(
            "checkout.session.completed",
            _session(donation.id, amount_total=2500, currency="USD"),
        )
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "completed"


def test_missing_amount_total_is_refused(db, stripe_env):
    recipient = _make_user(db, "recipient_noamount")
    donation = _make_donation(db, recipient)
    session = _session(donation.id)
    session["amount_total"] = None
    stub = _StubStripe(event=_event("checkout.session.completed", session))

    with patch.object(ds, "stripe", stub):
        with pytest.raises(PaymentDiscrepancy):
            DonationService.handle_webhook(db, b"{}", "sig")


def test_unpaid_session_leaves_the_donation_pending(db, stripe_env):
    """
    ``checkout.session.completed`` fires for delayed payment methods before
    the money settles. Completing on the event alone records a payment that
    has not happened.
    """
    recipient = _make_user(db, "recipient_unpaid")
    donation = _make_donation(db, recipient)
    stub = _StubStripe(
        event=_event(
            "checkout.session.completed",
            _session(donation.id, payment_status="unpaid"),
        )
    )

    with patch.object(ds, "stripe", stub):
        outcome = DonationService.handle_webhook(db, b"{}", "sig")

    assert outcome == "pending_payment"
    db.refresh(donation)
    assert donation.status == "pending"


# --------------------------------------------------------------------------
# Replays
# --------------------------------------------------------------------------


def test_replayed_event_is_a_no_op(db, stripe_env):
    """
    Stripe retries until it gets a 2xx. The old handler notified the recipient
    once per delivery.
    """
    recipient = _make_user(db, "recipient_replay")
    donation = _make_donation(db, recipient)
    event = _event("checkout.session.completed", _session(donation.id))
    stub = _StubStripe(event=event)

    with patch.object(ds, "stripe", stub):
        first = DonationService.handle_webhook(db, b"{}", "sig")
        second = DonationService.handle_webhook(db, b"{}", "sig")

    assert first == "completed"
    assert second == "duplicate"
    assert db.query(StripeWebhookEvent).count() == 1


def test_processed_event_records_the_donation_it_resolved_to(db, stripe_env):
    recipient = _make_user(db, "recipient_link")
    donation = _make_donation(db, recipient)
    stub = _StubStripe(
        event=_event("checkout.session.completed", _session(donation.id))
    )

    with patch.object(ds, "stripe", stub):
        DonationService.handle_webhook(db, b"{}", "sig")

    record = db.query(StripeWebhookEvent).one()
    assert record.donation_id == donation.id
    assert record.event_type == "checkout.session.completed"


def test_a_second_event_for_an_already_completed_donation_is_reported(db, stripe_env):
    recipient = _make_user(db, "recipient_second")
    donation = _make_donation(db, recipient, status="completed")
    stub = _StubStripe(
        event=_event(
            "checkout.session.completed", _session(donation.id), event_id="evt_other"
        )
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "already_completed"


# --------------------------------------------------------------------------
# Malformed references
# --------------------------------------------------------------------------


def test_non_uuid_client_reference_id_does_not_reach_the_query(db, stripe_env):
    """
    ``client_reference_id`` arrives in the request body. Passing a non-UUID
    string to a query against a UUID column raises a driver ``DataError``,
    which the router turned into a 500.
    """
    stub = _StubStripe(
        event=_event(
            "checkout.session.completed",
            _session(None) | {"client_reference_id": "'; DROP TABLE donations; --"},
        )
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "unmatched"


def test_unknown_donation_id_is_unmatched(db, stripe_env):
    stub = _StubStripe(
        event=_event("checkout.session.completed", _session(uuid.uuid4()))
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "unmatched"


def test_event_without_an_id_is_rejected(db, stripe_env):
    stub = _StubStripe(event={"type": "checkout.session.completed", "data": {}})

    with patch.object(ds, "stripe", stub):
        with pytest.raises(WebhookVerificationError):
            DonationService.handle_webhook(db, b"{}", "sig")


# --------------------------------------------------------------------------
# Failure events
# --------------------------------------------------------------------------


def test_async_payment_failed_marks_the_donation_failed(db, stripe_env):
    recipient = _make_user(db, "recipient_failed")
    donation = _make_donation(db, recipient)
    stub = _StubStripe(
        event=_event("checkout.session.async_payment_failed", _session(donation.id))
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "failed"

    db.refresh(donation)
    assert donation.status == "failed"


def test_expired_session_marks_the_donation_failed(db, stripe_env):
    recipient = _make_user(db, "recipient_expired")
    donation = _make_donation(db, recipient)
    stub = _StubStripe(
        event=_event("checkout.session.expired", _session(donation.id))
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "failed"

    db.refresh(donation)
    assert donation.status == "failed"


def test_failure_after_completion_is_left_for_review(db, stripe_env):
    """
    Reversing a completed donation is a refund question. Flipping the status
    back silently would lose the fact that money moved.
    """
    recipient = _make_user(db, "recipient_review")
    donation = _make_donation(db, recipient, status="completed")
    stub = _StubStripe(
        event=_event("checkout.session.async_payment_failed", _session(donation.id))
    )

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "needs_review"

    db.refresh(donation)
    assert donation.status == "completed"


def test_unhandled_event_type_is_ignored(db, stripe_env):
    stub = _StubStripe(event=_event("customer.created", {}))

    with patch.object(ds, "stripe", stub):
        assert DonationService.handle_webhook(db, b"{}", "sig") == "ignored"


# --------------------------------------------------------------------------
# Checkout
# --------------------------------------------------------------------------


def test_checkout_rejects_a_self_donation(db, stripe_env):
    user = _make_user(db, "self_donor")

    with patch.object(ds, "stripe", _StubStripe()):
        with pytest.raises(ValueError, match="yourself"):
            DonationService.create_checkout_session(
                db,
                DonationCreate(recipient_id=user.id, amount=2500),
                donor_id=user.id,
            )


def test_checkout_rejects_an_unknown_recipient(db, stripe_env):
    with patch.object(ds, "stripe", _StubStripe()):
        with pytest.raises(ValueError, match="Recipient not found"):
            DonationService.create_checkout_session(
                db,
                DonationCreate(recipient_id=uuid.uuid4(), amount=2500),
                donor_id=None,
            )


def test_checkout_marks_the_donation_failed_when_stripe_errors(db, stripe_env):
    recipient = _make_user(db, "recipient_stripe_err")
    stub = _StubStripe()
    stub.checkout.Session.create.side_effect = RuntimeError("stripe is down")

    with patch.object(ds, "stripe", stub):
        with pytest.raises(RuntimeError):
            DonationService.create_checkout_session(
                db,
                DonationCreate(recipient_id=recipient.id, amount=2500),
                donor_id=None,
            )

    donation = db.query(Donation).filter(Donation.recipient_id == recipient.id).one()
    assert donation.status == "failed"


def test_checkout_returns_the_session_url(db, stripe_env):
    recipient = _make_user(db, "recipient_url")
    stub = _StubStripe()
    stub.checkout.Session.create.return_value = {
        "id": "cs_created",
        "url": "https://checkout.stripe.test/cs_created",
    }

    with patch.object(ds, "stripe", stub):
        url = DonationService.create_checkout_session(
            db,
            DonationCreate(recipient_id=recipient.id, amount=2500),
            donor_id=None,
        )

    assert url == "https://checkout.stripe.test/cs_created"
    donation = db.query(Donation).filter(Donation.recipient_id == recipient.id).one()
    assert donation.stripe_session_id == "cs_created"
    assert donation.status == "pending"


# --------------------------------------------------------------------------
# Schema bounds
# --------------------------------------------------------------------------


@pytest.mark.parametrize("amount", [0, -1, -5000, 49, 1_000_001])
def test_out_of_range_amounts_are_rejected_before_a_row_is_written(amount):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DonationCreate(recipient_id=uuid.uuid4(), amount=amount)


@pytest.mark.parametrize("amount", [50, 2500, 1_000_000])
def test_in_range_amounts_are_accepted(amount):
    payload = DonationCreate(recipient_id=uuid.uuid4(), amount=amount)
    assert payload.amount == amount


def test_blank_message_normalises_to_none():
    payload = DonationCreate(recipient_id=uuid.uuid4(), amount=2500, message="   ")
    assert payload.message is None
