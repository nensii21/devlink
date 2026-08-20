# Messaging authorization

Every route under `/api/messages` acts on a conversation. The rule is one line:

> A caller may only act on a conversation they are a member of.

Membership is a row in `conversation_members`. There is no "public" conversation
and no read-only observer role — if you are not in the `ConversationMember`
table for a conversation, every route answers `403`.

## Where the check happens

`app/routers/messages.py`. The router is the enforcement point, and it enforces
in one of three ways depending on where the conversation id comes from.

**1. Path parameter — `require_conversation_member`.**

```python
def list_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(require_conversation_member),
): ...
```

The dependency both authenticates the caller and checks membership, and it
returns the caller. A route that needs `current_user` gets it *from* the check,
so there is no way to take the user and forget the check — which is how the
gap in #1234 happened in the first place.

**2. Request body — `_assert_conversation_member`.**

`POST /messages/`, `POST /messages/read/bulk` and `POST /messages/bulk-deliver`
carry the conversation id in the body, out of reach of a path-parameter
dependency. They call the helper explicitly, before any write.

**3. Message id — `_member_message_or_404`.**

`GET /messages/{id}`, `/pin`, `/unpin` and the edit/delete/restore family reach
the conversation only through the message. The helper resolves the message
(`404` if it does not exist) and then checks membership of its conversation.

## Membership is not authorship

Two separate checks, both load-bearing:

| | |
|---|---|
| **Membership** | read the thread, send into it, pin, mark read |
| **Authorship** | edit, delete, restore — your own messages only |

They are not redundant in either direction. A member who did not write a
message still cannot edit it. And someone removed from a conversation keeps
their `sender_id` on everything they wrote there — an authorship-only check let
a removed member go on editing and deleting inside a thread they had left, so
edit/delete requires membership *and* authorship.

## Why `403` and not `404`

`403 "You are not a member of this conversation"` is what the read-receipt
routes have returned since they were written, and their tests assert it. Using
`404` on the routes fixed here would have been marginally better at not
confirming that a conversation exists, at the cost of two different answers to
the same question depending on which route you asked. Conversation ids are
UUIDs, so enumeration is not the threat model; consistency is worth more.

## Bulk by id is scoped, not refused

`POST /messages/read/bulk` and `/bulk-deliver` accept either a
`conversation_id` or a list of `message_ids`. A caller may legitimately pass
ids spanning several of their own conversations, so the id form is *filtered*
to conversations the caller belongs to (`MessageService.bulk_mark_as_read`)
rather than rejected wholesale. Passing a stranger's message id is not an
error; it updates nothing.

## Not covered here

`/api/conversations` has its own routes for creating conversations and adding
and removing members. This document is about `/api/messages` only.

## Tests

`backend/tests/test_message_authorization.py` — every route checked three ways:
anonymous, authenticated non-member, and member. The third is not decoration;
an authorization change that locks out the people who are allowed in is not a
fix.
