## Summary

Closes #995

This PR enhances the Organization Profile by adding several key missing sections, giving users a more comprehensive view of each organization.

## Changes

- **OrganizationHeader**: Added socialLinks prop to display Twitter, GitHub, and LinkedIn icons alongside the "Visit Website" button.
- **OrganizationProfile**: 
  - Added 	echnologies rendering within the "About Us" tab using badge UI.
  - Introduced a new "Activity Feed" tab (ctivity) to display a timeline of organization updates.
- **_app.organizations..tsx**: Updated the mockOrgData to pass 	echnologies, socialLinks, and ctivityFeed data to the profile component.

## Acceptance Criteria

- [x] Add About, Open positions, Featured projects, Team members, Technologies, Social links, Website, Activity feed

## Impact & Side Effects

No breaking changes or side effects.

## How to Test

1. Navigate to an organization profile page (e.g., /organizations/1).
2. Verify that social links are displayed in the header.
3. Verify that the "About Us" tab shows a "Technologies We Use" section.
4. Verify that the new "Activity Feed" tab exists and displays recent updates.

## Quality Checklist

- [x] Linting passes.
- [x] Type checking passes.
