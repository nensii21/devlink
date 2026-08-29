from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook_dispatch_params_headers_type_0 import (
        WebhookDispatchParamsHeadersType0,
    )
    from ..models.webhook_dispatch_params_payload import WebhookDispatchParamsPayload


T = TypeVar("T", bound="WebhookDispatchParams")


@_attrs_define
class WebhookDispatchParams:
    """
    Attributes:
        event_type (str): Event action name e.g. project.created, user.updated
        target_url (str): Destination webhook URL
        payload (WebhookDispatchParamsPayload): JSON payload data
        headers (None | Unset | WebhookDispatchParamsHeadersType0): Custom HTTP headers
        max_retries (int | Unset): Max retry attempts limit Default: 5.
    """

    event_type: str
    target_url: str
    payload: WebhookDispatchParamsPayload
    headers: None | Unset | WebhookDispatchParamsHeadersType0 = UNSET
    max_retries: int | Unset = 5
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.webhook_dispatch_params_headers_type_0 import (
            WebhookDispatchParamsHeadersType0,
        )

        event_type = self.event_type

        target_url = self.target_url

        payload = self.payload.to_dict()

        headers: dict[str, Any] | None | Unset
        if isinstance(self.headers, Unset):
            headers = UNSET
        elif isinstance(self.headers, WebhookDispatchParamsHeadersType0):
            headers = self.headers.to_dict()
        else:
            headers = self.headers

        max_retries = self.max_retries

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "event_type": event_type,
                "target_url": target_url,
                "payload": payload,
            }
        )
        if headers is not UNSET:
            field_dict["headers"] = headers
        if max_retries is not UNSET:
            field_dict["max_retries"] = max_retries

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_dispatch_params_headers_type_0 import (
            WebhookDispatchParamsHeadersType0,
        )
        from ..models.webhook_dispatch_params_payload import (
            WebhookDispatchParamsPayload,
        )

        d = dict(src_dict)
        event_type = d.pop("event_type")

        target_url = d.pop("target_url")

        payload = WebhookDispatchParamsPayload.from_dict(d.pop("payload"))

        def _parse_headers(
            data: object,
        ) -> None | Unset | WebhookDispatchParamsHeadersType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                headers_type_0 = WebhookDispatchParamsHeadersType0.from_dict(data)

                return headers_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WebhookDispatchParamsHeadersType0, data)

        headers = _parse_headers(d.pop("headers", UNSET))

        max_retries = d.pop("max_retries", UNSET)

        webhook_dispatch_params = cls(
            event_type=event_type,
            target_url=target_url,
            payload=payload,
            headers=headers,
            max_retries=max_retries,
        )

        webhook_dispatch_params.additional_properties = d
        return webhook_dispatch_params

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
