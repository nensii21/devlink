from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.duplicate_suggestion_response import DuplicateSuggestionResponse


T = TypeVar("T", bound="DuplicateCheckResponse")


@_attrs_define
class DuplicateCheckResponse:
    """
    Attributes:
        has_duplicates (bool):
        suggestions (list[DuplicateSuggestionResponse]):
        checked_count (int):
        threshold (float):
    """

    has_duplicates: bool
    suggestions: list[DuplicateSuggestionResponse]
    checked_count: int
    threshold: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        has_duplicates = self.has_duplicates

        suggestions = []
        for suggestions_item_data in self.suggestions:
            suggestions_item = suggestions_item_data.to_dict()
            suggestions.append(suggestions_item)

        checked_count = self.checked_count

        threshold = self.threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "has_duplicates": has_duplicates,
                "suggestions": suggestions,
                "checked_count": checked_count,
                "threshold": threshold,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.duplicate_suggestion_response import DuplicateSuggestionResponse

        d = dict(src_dict)
        has_duplicates = d.pop("has_duplicates")

        suggestions = []
        _suggestions = d.pop("suggestions")
        for suggestions_item_data in _suggestions:
            suggestions_item = DuplicateSuggestionResponse.from_dict(
                suggestions_item_data
            )

            suggestions.append(suggestions_item)

        checked_count = d.pop("checked_count")

        threshold = d.pop("threshold")

        duplicate_check_response = cls(
            has_duplicates=has_duplicates,
            suggestions=suggestions,
            checked_count=checked_count,
            threshold=threshold,
        )

        duplicate_check_response.additional_properties = d
        return duplicate_check_response

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
