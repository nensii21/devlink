from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.conversation_starter_suggestion import ConversationStarterSuggestion


T = TypeVar("T", bound="ConversationStarterResponse")


@_attrs_define
class ConversationStarterResponse:
    """Response containing conversation starter suggestions.

    Attributes:
        suggestions (list[ConversationStarterSuggestion]): 3-5 context-aware conversation starter suggestions
        target_user_id (UUID):
        target_user_name (str):
    """

    suggestions: list[ConversationStarterSuggestion]
    target_user_id: UUID
    target_user_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        suggestions = []
        for suggestions_item_data in self.suggestions:
            suggestions_item = suggestions_item_data.to_dict()
            suggestions.append(suggestions_item)

        target_user_id = str(self.target_user_id)

        target_user_name = self.target_user_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "suggestions": suggestions,
                "target_user_id": target_user_id,
                "target_user_name": target_user_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversation_starter_suggestion import (
            ConversationStarterSuggestion,
        )

        d = dict(src_dict)
        suggestions = []
        _suggestions = d.pop("suggestions")
        for suggestions_item_data in _suggestions:
            suggestions_item = ConversationStarterSuggestion.from_dict(
                suggestions_item_data
            )

            suggestions.append(suggestions_item)

        target_user_id = UUID(d.pop("target_user_id"))

        target_user_name = d.pop("target_user_name")

        conversation_starter_response = cls(
            suggestions=suggestions,
            target_user_id=target_user_id,
            target_user_name=target_user_name,
        )

        conversation_starter_response.additional_properties = d
        return conversation_starter_response

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
