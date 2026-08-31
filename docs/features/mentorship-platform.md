# Mentorship Platform

The DevLink Mentorship Platform enables developers to connect for knowledge sharing, career guidance, and technical pairing. It provides robust tools for skill-based matching, availability scheduling, and session management.

## Core Features

### Skill-Based Matching
The platform uses a weighted similarity scoring algorithm (`find_matches`) to pair mentees with the most relevant mentors.
- **Required Expertise (Weight 10x)**: Matches against skills the mentee explicitly needs help with.
- **General Overlap (Weight 2x)**: Matches against general background skills shared between both parties.
- **Mentor Rating**: A fractional boost based on aggregate historical feedback scores ensures highly-rated mentors float to the top of equivalent technical matches.

### Availability & Conflict Prevention
Mentors define `TimeWindow` blocks representing their weekly availability.
When a mentee requests a session:
1. The requested time must fall entirely within an open `TimeWindow`.
2. The `MentorshipService` actively checks the schedule for double-booking. Any overlapping sessions in a `CONFIRMED` or `IN_PROGRESS` state will instantly reject the new request.

### Structured Feedback Loop
Instead of generic 5-star ratings, the platform enforces `StructuredFeedback` across three distinct axes:
- `communication_score`
- `technical_accuracy_score`
- `helpfulness_score`

These scores are averaged and factored into a moving average for the mentor's global `rating_score`.

### Notification Hooks
The `MentorshipService` exposes a lightweight event bus via `on_session_status_changed`. Core backend systems (like email or WebSocket push notifications) can register callbacks here to seamlessly broadcast status changes (`REQUESTED`, `CONFIRMED`, `CANCELLED`) to users without tightly coupling the domain logic.
