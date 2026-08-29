from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.issue_difficulty import IssueDifficulty
from ..models.issue_priority import IssuePriority
from ..models.issue_status import IssueStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.duplicate_suggestion_response import DuplicateSuggestionResponse
    from ..models.issue_author_response import IssueAuthorResponse


T = TypeVar("T", bound="IssueDetailResponse")


@_attrs_define
class IssueDetailResponse:
    """
    Attributes:
        title (str):
        description (str):
        id (UUID):
        project_id (UUID):
        author_id (UUID):
        status (IssueStatus):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        priority (IssuePriority | Unset):
        labels (None | str | Unset):
        difficulty (IssueDifficulty | None | Unset):
        difficulty_confidence (float | None | Unset):
        difficulty_manual_override (bool | Unset):  Default: False.
        is_duplicate_checked (bool | Unset):  Default: False.
        author (IssueAuthorResponse | None | Unset):
        duplicate_suggestions (list[DuplicateSuggestionResponse] | Unset):
    """

    title: str
    description: str
    id: UUID
    project_id: UUID
    author_id: UUID
    status: IssueStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    priority: IssuePriority | Unset = UNSET
    labels: None | str | Unset = UNSET
    difficulty: IssueDifficulty | None | Unset = UNSET
    difficulty_confidence: float | None | Unset = UNSET
    difficulty_manual_override: bool | Unset = False
    is_duplicate_checked: bool | Unset = False
    author: IssueAuthorResponse | None | Unset = UNSET
    duplicate_suggestions: list[DuplicateSuggestionResponse] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.issue_author_response import IssueAuthorResponse

        title = self.title

        description = self.description

        id = str(self.id)

        project_id = str(self.project_id)

        author_id = str(self.author_id)

        status = self.status.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        priority: str | Unset = UNSET
        if not isinstance(self.priority, Unset):
            priority = self.priority.value

        labels: None | str | Unset
        if isinstance(self.labels, Unset):
            labels = UNSET
        else:
            labels = self.labels

        difficulty: None | str | Unset
        if isinstance(self.difficulty, Unset):
            difficulty = UNSET
        elif isinstance(self.difficulty, IssueDifficulty):
            difficulty = self.difficulty.value
        else:
            difficulty = self.difficulty

        difficulty_confidence: float | None | Unset
        if isinstance(self.difficulty_confidence, Unset):
            difficulty_confidence = UNSET
        else:
            difficulty_confidence = self.difficulty_confidence

        difficulty_manual_override = self.difficulty_manual_override

        is_duplicate_checked = self.is_duplicate_checked

        author: dict[str, Any] | None | Unset
        if isinstance(self.author, Unset):
            author = UNSET
        elif isinstance(self.author, IssueAuthorResponse):
            author = self.author.to_dict()
        else:
            author = self.author

        duplicate_suggestions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.duplicate_suggestions, Unset):
            duplicate_suggestions = []
            for duplicate_suggestions_item_data in self.duplicate_suggestions:
                duplicate_suggestions_item = duplicate_suggestions_item_data.to_dict()
                duplicate_suggestions.append(duplicate_suggestions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "description": description,
                "id": id,
                "project_id": project_id,
                "author_id": author_id,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if priority is not UNSET:
            field_dict["priority"] = priority
        if labels is not UNSET:
            field_dict["labels"] = labels
        if difficulty is not UNSET:
            field_dict["difficulty"] = difficulty
        if difficulty_confidence is not UNSET:
            field_dict["difficulty_confidence"] = difficulty_confidence
        if difficulty_manual_override is not UNSET:
            field_dict["difficulty_manual_override"] = difficulty_manual_override
        if is_duplicate_checked is not UNSET:
            field_dict["is_duplicate_checked"] = is_duplicate_checked
        if author is not UNSET:
            field_dict["author"] = author
        if duplicate_suggestions is not UNSET:
            field_dict["duplicate_suggestions"] = duplicate_suggestions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.duplicate_suggestion_response import DuplicateSuggestionResponse
        from ..models.issue_author_response import IssueAuthorResponse

        d = dict(src_dict)
        title = d.pop("title")

        description = d.pop("description")

        id = UUID(d.pop("id"))

        project_id = UUID(d.pop("project_id"))

        author_id = UUID(d.pop("author_id"))

        status = IssueStatus(d.pop("status"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        _priority = d.pop("priority", UNSET)
        priority: IssuePriority | Unset
        if isinstance(_priority, Unset):
            priority = UNSET
        else:
            priority = IssuePriority(_priority)

        def _parse_labels(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        labels = _parse_labels(d.pop("labels", UNSET))

        def _parse_difficulty(data: object) -> IssueDifficulty | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                difficulty_type_0 = IssueDifficulty(data)

                return difficulty_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(IssueDifficulty | None | Unset, data)

        difficulty = _parse_difficulty(d.pop("difficulty", UNSET))

        def _parse_difficulty_confidence(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        difficulty_confidence = _parse_difficulty_confidence(
            d.pop("difficulty_confidence", UNSET)
        )

        difficulty_manual_override = d.pop("difficulty_manual_override", UNSET)

        is_duplicate_checked = d.pop("is_duplicate_checked", UNSET)

        def _parse_author(data: object) -> IssueAuthorResponse | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                author_type_0 = IssueAuthorResponse.from_dict(data)

                return author_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(IssueAuthorResponse | None | Unset, data)

        author = _parse_author(d.pop("author", UNSET))

        _duplicate_suggestions = d.pop("duplicate_suggestions", UNSET)
        duplicate_suggestions: list[DuplicateSuggestionResponse] | Unset = UNSET
        if _duplicate_suggestions is not UNSET:
            duplicate_suggestions = []
            for duplicate_suggestions_item_data in _duplicate_suggestions:
                duplicate_suggestions_item = DuplicateSuggestionResponse.from_dict(
                    duplicate_suggestions_item_data
                )

                duplicate_suggestions.append(duplicate_suggestions_item)

        issue_detail_response = cls(
            title=title,
            description=description,
            id=id,
            project_id=project_id,
            author_id=author_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            priority=priority,
            labels=labels,
            difficulty=difficulty,
            difficulty_confidence=difficulty_confidence,
            difficulty_manual_override=difficulty_manual_override,
            is_duplicate_checked=is_duplicate_checked,
            author=author,
            duplicate_suggestions=duplicate_suggestions,
        )

        issue_detail_response.additional_properties = d
        return issue_detail_response

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
