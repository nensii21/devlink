from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_dlq_response_headers_type_0 import (
        WebhookDLQResponseHeadersType0,
    )
    from ..models.webhook_dlq_response_payload import WebhookDLQResponsePayload


T = TypeVar("T", bound="WebhookDLQResponse")


@_attrs_define
class WebhookDLQResponse:
    """
    Attributes:
        id (UUID):
        delivery_id (UUID):
        event_type (str):
        target_url (str):
        payload (WebhookDLQResponsePayload):
        total_attempts (int):
        failure_reason (str):
        failed_at (datetime.datetime):
        is_replayed (bool):
        headers (None | Unset | WebhookDLQResponseHeadersType0):
        replayed_at (datetime.datetime | None | Unset):
    """

    id: UUID
    delivery_id: UUID
    event_type: str
    target_url: str
    payload: WebhookDLQResponsePayload
    total_attempts: int
    failure_reason: str
    failed_at: datetime.datetime
    is_replayed: bool
    headers: None | Unset | WebhookDLQResponseHeadersType0 = UNSET
    replayed_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_dlq_response_headers_type_0 import (
            WebhookDLQResponseHeadersType0,
        )

        id = str(self.id)

        delivery_id = str(self.delivery_id)

        event_type = self.event_type

        target_url = self.target_url

        payload = self.payload.to_dict()

        total_attempts = self.total_attempts

        failure_reason = self.failure_reason

        failed_at = self.failed_at.isoformat()

        is_replayed = self.is_replayed

        headers: dict[str, Any] | None | Unset
        if isinstance(self.headers, Unset):
            headers = UNSET
        elif isinstance(self.headers, WebhookDLQResponseHeadersType0):
            headers = self.headers.to_dict()
        else:
            headers = self.headers

        replayed_at: None | str | Unset
        if isinstance(self.replayed_at, Unset):
            replayed_at = UNSET
        elif isinstance(self.replayed_at, datetime.datetime):
            replayed_at = self.replayed_at.isoformat()
        else:
            replayed_at = self.replayed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "delivery_id": delivery_id,
                "event_type": event_type,
                "target_url": target_url,
                "payload": payload,
                "total_attempts": total_attempts,
                "failure_reason": failure_reason,
                "failed_at": failed_at,
                "is_replayed": is_replayed,
            }
        )
        if headers is not UNSET:
            field_dict["headers"] = headers
        if replayed_at is not UNSET:
            field_dict["replayed_at"] = replayed_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_dlq_response_headers_type_0 import (
            WebhookDLQResponseHeadersType0,
        )
        from ..models.webhook_dlq_response_payload import WebhookDLQResponsePayload

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        delivery_id = UUID(d.pop("delivery_id"))

        event_type = d.pop("event_type")

        target_url = d.pop("target_url")

        payload = WebhookDLQResponsePayload.from_dict(d.pop("payload"))

        total_attempts = d.pop("total_attempts")

        failure_reason = d.pop("failure_reason")

        failed_at = datetime.datetime.fromisoformat(d.pop("failed_at"))

        is_replayed = d.pop("is_replayed")

        def _parse_headers(
            data: object,
        ) -> None | Unset | WebhookDLQResponseHeadersType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                headers_type_0 = WebhookDLQResponseHeadersType0.from_dict(data)

                return headers_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WebhookDLQResponseHeadersType0, data)

        headers = _parse_headers(d.pop("headers", UNSET))

        def _parse_replayed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                replayed_at_type_0 = datetime.datetime.fromisoformat(data)

                return replayed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        replayed_at = _parse_replayed_at(d.pop("replayed_at", UNSET))

        webhook_dlq_response = cls(
            id=id,
            delivery_id=delivery_id,
            event_type=event_type,
            target_url=target_url,
            payload=payload,
            total_attempts=total_attempts,
            failure_reason=failure_reason,
            failed_at=failed_at,
            is_replayed=is_replayed,
            headers=headers,
            replayed_at=replayed_at,
        )

        webhook_dlq_response.additional_properties = d
        return webhook_dlq_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
