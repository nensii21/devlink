from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.template_preview_request_variables import (
        TemplatePreviewRequestVariables,
    )


T = TypeVar("T", bound="TemplatePreviewRequest")


@_attrs_define
class TemplatePreviewRequest:
    """
    Attributes:
        title_template (str):
        message_template (str):
        variables (TemplatePreviewRequestVariables):
    """

    title_template: str
    message_template: str
    variables: TemplatePreviewRequestVariables
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title_template = self.title_template

        message_template = self.message_template

        variables = self.variables.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title_template": title_template,
                "message_template": message_template,
                "variables": variables,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template_preview_request_variables import (
            TemplatePreviewRequestVariables,
        )

        d = dict(src_dict)
        title_template = d.pop("title_template")

        message_template = d.pop("message_template")

        variables = TemplatePreviewRequestVariables.from_dict(d.pop("variables"))

        template_preview_request = cls(
            title_template=title_template,
            message_template=message_template,
            variables=variables,
        )

        template_preview_request.additional_properties = d
        return template_preview_request

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
