from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_delivery_status import WebhookDeliveryStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_delivery_response_headers_type_0 import (
        WebhookDeliveryResponseHeadersType0,
    )
    from ..models.webhook_delivery_response_payload import (
        WebhookDeliveryResponsePayload,
    )


T = TypeVar("T", bound="WebhookDeliveryResponse")


@_attrs_define
class WebhookDeliveryResponse:
    """
    Attributes:
        id (UUID):
        event_type (str):
        target_url (str):
        payload (WebhookDeliveryResponsePayload):
        status (WebhookDeliveryStatus):
        attempts (int):
        max_retries (int):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        headers (None | Unset | WebhookDeliveryResponseHeadersType0):
        next_retry_at (datetime.datetime | None | Unset):
        last_attempt_at (datetime.datetime | None | Unset):
        response_status_code (int | None | Unset):
        response_body (None | str | Unset):
        error_message (None | str | Unset):
    """

    id: UUID
    event_type: str
    target_url: str
    payload: WebhookDeliveryResponsePayload
    status: WebhookDeliveryStatus
    attempts: int
    max_retries: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    headers: None | Unset | WebhookDeliveryResponseHeadersType0 = UNSET
    next_retry_at: datetime.datetime | None | Unset = UNSET
    last_attempt_at: datetime.datetime | None | Unset = UNSET
    response_status_code: int | None | Unset = UNSET
    response_body: None | str | Unset = UNSET
    error_message: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_delivery_response_headers_type_0 import (
            WebhookDeliveryResponseHeadersType0,
        )

        id = str(self.id)

        event_type = self.event_type

        target_url = self.target_url

        payload = self.payload.to_dict()

        status = self.status.value

        attempts = self.attempts

        max_retries = self.max_retries

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        headers: dict[str, Any] | None | Unset
        if isinstance(self.headers, Unset):
            headers = UNSET
        elif isinstance(self.headers, WebhookDeliveryResponseHeadersType0):
            headers = self.headers.to_dict()
        else:
            headers = self.headers

        next_retry_at: None | str | Unset
        if isinstance(self.next_retry_at, Unset):
            next_retry_at = UNSET
        elif isinstance(self.next_retry_at, datetime.datetime):
            next_retry_at = self.next_retry_at.isoformat()
        else:
            next_retry_at = self.next_retry_at

        last_attempt_at: None | str | Unset
        if isinstance(self.last_attempt_at, Unset):
            last_attempt_at = UNSET
        elif isinstance(self.last_attempt_at, datetime.datetime):
            last_attempt_at = self.last_attempt_at.isoformat()
        else:
            last_attempt_at = self.last_attempt_at

        response_status_code: int | None | Unset
        if isinstance(self.response_status_code, Unset):
            response_status_code = UNSET
        else:
            response_status_code = self.response_status_code

        response_body: None | str | Unset
        if isinstance(self.response_body, Unset):
            response_body = UNSET
        else:
            response_body = self.response_body

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "event_type": event_type,
                "target_url": target_url,
                "payload": payload,
                "status": status,
                "attempts": attempts,
                "max_retries": max_retries,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if headers is not UNSET:
            field_dict["headers"] = headers
        if next_retry_at is not UNSET:
            field_dict["next_retry_at"] = next_retry_at
        if last_attempt_at is not UNSET:
            field_dict["last_attempt_at"] = last_attempt_at
        if response_status_code is not UNSET:
            field_dict["response_status_code"] = response_status_code
        if response_body is not UNSET:
            field_dict["response_body"] = response_body
        if error_message is not UNSET:
            field_dict["error_message"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_delivery_response_headers_type_0 import (
            WebhookDeliveryResponseHeadersType0,
        )
        from ..models.webhook_delivery_response_payload import (
            WebhookDeliveryResponsePayload,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        event_type = d.pop("event_type")

        target_url = d.pop("target_url")

        payload = WebhookDeliveryResponsePayload.from_dict(d.pop("payload"))

        status = WebhookDeliveryStatus(d.pop("status"))

        attempts = d.pop("attempts")

        max_retries = d.pop("max_retries")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_headers(
            data: object,
        ) -> None | Unset | WebhookDeliveryResponseHeadersType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                headers_type_0 = WebhookDeliveryResponseHeadersType0.from_dict(data)

                return headers_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WebhookDeliveryResponseHeadersType0, data)

        headers = _parse_headers(d.pop("headers", UNSET))

        def _parse_next_retry_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_retry_at_type_0 = datetime.datetime.fromisoformat(data)

                return next_retry_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        next_retry_at = _parse_next_retry_at(d.pop("next_retry_at", UNSET))

        def _parse_last_attempt_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_attempt_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_attempt_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_attempt_at = _parse_last_attempt_at(d.pop("last_attempt_at", UNSET))

        def _parse_response_status_code(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        response_status_code = _parse_response_status_code(
            d.pop("response_status_code", UNSET)
        )

        def _parse_response_body(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        response_body = _parse_response_body(d.pop("response_body", UNSET))

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        webhook_delivery_response = cls(
            id=id,
            event_type=event_type,
            target_url=target_url,
            payload=payload,
            status=status,
            attempts=attempts,
            max_retries=max_retries,
            created_at=created_at,
            updated_at=updated_at,
            headers=headers,
            next_retry_at=next_retry_at,
            last_attempt_at=last_attempt_at,
            response_status_code=response_status_code,
            response_body=response_body,
            error_message=error_message,
        )

        webhook_delivery_response.additional_properties = d
        return webhook_delivery_response

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
