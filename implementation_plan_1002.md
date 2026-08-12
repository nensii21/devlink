# Feature: Payment history and invoice management

Closes #1002. This builds upon the Pro Subscription gating feature from #1001.

## Proposed Changes

### Backend

#### [NEW] `backend/app/models/payment_history.py`
Create a `PaymentHistory` model:
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key to users)
- `amount` (Integer, cents)
- `currency` (String, default "usd")
- `status` (String: succeeded, failed, pending)
- `invoice_url` (String)
- `created_at` (DateTime)

#### [MODIFY] `backend/app/models/user_subscription.py`
Add fields:
- `payment_method_brand` (String, e.g., "Visa")
- `payment_method_last4` (String, e.g., "4242")

#### [NEW] `backend/alembic/versions/xxxx_create_payment_history_table.py`
Migration for the new table and columns.

#### [NEW] `backend/app/routers/payments.py`
Create API endpoints:
- `GET /api/payments/history`: List payment history for current user.
- `POST /api/payments/update-method`: Simulate updating the default payment method (changes last4 and brand).

#### [MODIFY] `backend/app/routers/subscriptions.py`
Add endpoints:
- `POST /api/subscriptions/cancel`: Sets the `status` of `UserSubscription` to "canceled".

#### [MODIFY] `backend/app/main.py`
Register the `payments.py` router.

### Frontend

#### [MODIFY] `frontend/src/api/modules/subscriptions.ts`
Add the cancel subscription API call.

#### [NEW] `frontend/src/api/modules/payments.ts`
Add API calls for:
- `getPaymentHistory()`
- `updatePaymentMethod(data)`

#### [MODIFY] `frontend/src/components/settings/SubscriptionSection.tsx`
Enhance the existing component to:
- Show current subscription status with an option to **Cancel subscription** (if active).
- Show the current payment method (e.g. Visa ending in 4242) and an option to **Update payment method**.
- Add a section below for **Payment History**, displaying a table of past payments with a **Download Invoice** button.

## Open Questions
- Since there's no real payment processor integration yet, I will mock the update method and cancel operations directly in the database. Is that acceptable?
- For invoice downloads, I'll return a mock URL or a simple generated blob.

## Verification Plan
- Run `alembic upgrade head`.
- Log in and navigate to Settings > Billing.
- Upgrade to Pro (from #1001).
- Try updating the payment method (should change the last4 display).
- View mock payment history items.
- Try canceling the subscription.
