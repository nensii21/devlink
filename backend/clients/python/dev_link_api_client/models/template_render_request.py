from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.template_render_request_variables import (
        TemplateRenderRequestVariables,
    )


T = TypeVar("T", bound="TemplateRenderRequest")


@_attrs_define
class TemplateRenderRequest:
    """
    Attributes:
        event_type (str):
        variables (TemplateRenderRequestVariables):
    """

    event_type: str
    variables: TemplateRenderRequestVariables
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_type = self.event_type

        variables = self.variables.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "event_type": event_type,
                "variables": variables,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template_render_request_variables import (
            TemplateRenderRequestVariables,
        )

        d = dict(src_dict)
        event_type = d.pop("event_type")

        variables = TemplateRenderRequestVariables.from_dict(d.pop("variables"))

        template_render_request = cls(
            event_type=event_type,
            variables=variables,
        )

        template_render_request.additional_properties = d
        return template_render_request

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
