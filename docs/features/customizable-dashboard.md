# Customizable Dashboard Widgets (#754)

DevLink provides a fully personalized dashboard experience allowing users to customize their widget layout, prioritize critical sections, hide unneeded items, and persist settings across devices.

---

## Features

### 1. Drag-and-Drop Reordering
- Native HTML5 smooth drag and drop with clear drop indicator states.
- Dedicated drag handles (`GripVertical`) and responsive card scaling.
- Accessible alternative controls with Move Up (`↑`) and Move Down (`↓`) action buttons.

### 2. Pin and Unpin Sections
- Pin high-priority widgets to a prominent top row grid.
- Visual pinned badges and one-click pin/unpin toggles.

### 3. Hide and Show Widgets
- Hide any widget with one click (`EyeOff`).
- Access the **Manage Widgets** dialog modal to review all widgets, toggle visibility switches, and read widget descriptions.

### 4. Layout Persistence
- Saved to the user profile in the backend database via `PUT /api/users/me/dashboard-layout`.
- Synchronized with `localStorage` for zero-flicker offline and fast initial loads.

### 5. Reset to Default
- One-click restore to the default standard DevLink dashboard layout (`DELETE /api/users/me/dashboard-layout`).

---

## Backend API Endpoints

- `GET /api/users/me/dashboard-layout` -> Returns `{ widgets: DashboardWidgetLayout[], is_customized: bool }`
- `PUT /api/users/me/dashboard-layout` -> Updates and saves the customized layout.
- `DELETE /api/users/me/dashboard-layout` -> Resets the layout back to default settings.

---

## Registered Widgets

1. `current-projects`: Active projects the user manages or collaborates on.
2. `ai-suggestions`: Teammate suggestions, events, and profile optimization tips.
3. `quick-actions`: Quick creation shortcuts.
4. `recent-activity`: Timeline of comments, team invites, and flare updates.
5. `upcoming`: Deadlines, meetups, and hackathons calendar.
6. `notifications`: Alert updates and discussion pings.
7. `upcoming-events`: Scheduled community events.
8. `upgrade-plan`: Pro highlights and upgrade card.
