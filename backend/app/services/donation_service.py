import os
import stripe
from sqlalchemy.orm import Session
from app.models.donation import Donation
from app.models.user import User
from app.schemas.donation import DonationCreate
import uuid

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock_key")

class DonationService:
    @staticmethod
    def create_checkout_session(db: Session, donation_data: DonationCreate, donor_id: uuid.UUID | None) -> str:
        recipient = db.query(User).filter(User.id == donation_data.recipient_id).first()
        if not recipient:
            raise ValueError("Recipient not found")

        donation = Donation(
            donor_id=donor_id,
            recipient_id=donation_data.recipient_id,
            amount=donation_data.amount,
            currency="usd",
            status="pending",
            message=donation_data.message
        )
        db.add(donation)
        db.commit()
        db.refresh(donation)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Donation to {recipient.first_name} {recipient.last_name}',
                            'description': donation_data.message or 'Thank you for your support!',
                        },
                        'unit_amount': donation_data.amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f'{frontend_url}/profile/{recipient.username}?donation=success',
                cancel_url=f'{frontend_url}/profile/{recipient.username}?donation=cancelled',
                client_reference_id=str(donation.id)
            )
            
            donation.stripe_session_id = session.id
            db.commit()
            
            return session.url
        except Exception as e:
            donation.status = "failed"
            db.commit()
            raise Exception(f"Failed to create Stripe session: {str(e)}")

    @staticmethod
    def handle_webhook(db: Session, payload: bytes, sig_header: str) -> None:
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock_secret")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            donation_id = session.get('client_reference_id')
            
            if donation_id:
                donation = db.query(Donation).filter(Donation.id == donation_id).first()
                if donation:
                    donation.status = 'completed'
                    db.commit()
                    
                    # Notify the recipient
                    from app.models.notification import NotificationType
                    from app.schemas.notification import NotificationCreate
                    from app.services.notification_service import NotificationService
                    
                    notif = NotificationCreate(
                        recipient_id=donation.recipient_id,
                        type=NotificationType.MESSAGE,
                        title="New Donation Received!",
                        message=f"You received a donation of ${donation.amount / 100:.2f}!",
                        action_url=f"/donations",
                    )
                    NotificationService.create_notification(
                        db=db,
                        recipient_id=donation.recipient_id,
                        sender_id=donation.donor_id,
                        notification=notif
                    )
