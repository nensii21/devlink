Hi maintainers!

I have implemented the Payment History, Invoice Management, and extended Subscription lifecycle capabilities.

### Technical Analysis
- **Core Architecture Change:** Introduced the `PaymentHistory` model with appropriate DB migrations to cleanly separate transaction records from the active subscription state. 
- **Core Backend Feature:** Implemented `update_payment_method` and `cancel_subscription` logic directly interacting with DB abstractions, establishing endpoints for future payment gateway (Stripe/Braintree) drop-in integration while ensuring DB state accurately reflects the lifecycle.
- **Frontend Refactoring:** Enriched the `SubscriptionSection` component using React Query to seamlessly fetch payment histories, handle mock card token operations via modal forms, and trigger robust 403-aware queries, establishing a solid user-facing self-serve portal.

Because this PR builds essential backend capabilities regarding financial data (payment histories, subscription lifecycle events) and adds complex frontend modals, I request the `ECSoC26`, `Level 3`, `good-backend`, and `good-ui` labels.

Could you please review and apply these labels? Thank you!
