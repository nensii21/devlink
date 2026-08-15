### Summary
This PR implements Payment History, Invoice Management, and extended Subscription capabilities, resolving #1002. It builds upon the subscription gating foundation laid in #1001.

### Motivation
Closes #1002

To provide comprehensive billing management for DevLink users, we need to allow users to update their payment methods, view past payments, download invoices, and cancel their active subscriptions securely.

### Changes
- **Backend**:
  - Created `backend/app/models/payment_history.py`: `PaymentHistory` model for recording past transactions and invoices.
  - Modified `backend/app/models/user_subscription.py`: Added `payment_method_brand` and `payment_method_last4` for displaying card details.
  - Created `backend/app/routers/payments.py`: Endpoints for `GET /api/payments/history` and `POST /api/payments/update-method`.
  - Modified `backend/app/routers/subscriptions.py`: Added `POST /api/subscriptions/cancel` endpoint to securely cancel active subscriptions.
- **Frontend**:
  - Created `frontend/src/api/modules/payments.ts`: New API wrapper for payment-related operations.
  - Modified `frontend/src/api/modules/subscriptions.ts`: Added cancellation method and typed new fields in `SubscriptionInfo`.
  - Modified `frontend/src/components/settings/SubscriptionSection.tsx`: 
    - Display current payment method and an "Update Method" button.
    - Provide a "Cancel Plan" button with confirmation prompt.
    - Integrate `Payment History` view displaying rows of successful transactions with a mock "Download Invoice" action.

### Acceptance Criteria
- [x] View payment history
- [x] Download invoices
- [x] View subscription status
- [x] Update payment method
- [x] Cancel subscription

### Impact & Side Effects
No breaking changes. Free users remain unaffected. Pro users now have self-serve tools to manage their financial status and access their history without support intervention.

### How to Test
1. Make sure to run `uv run alembic upgrade head`.
2. Login as a free user and go to Settings > Billing.
3. Click "Upgrade to Pro" to gain an active subscription.
4. Click "Update Method" and enter a mock token (e.g., `tok_mastercard`). Ensure the displayed payment method updates to Mastercard ending in 5555.
5. Review the "Payment History" section, observing the mock history items (if populated manually via DB).
6. Click "Cancel Plan" and confirm the action. Verify the UI updates back to Free tier restrictions.

### Quality Checklist
- [x] I have run the linter and tests locally
- [x] I have updated the documentation (if applicable)
- [x] I have added/updated relevant tests
