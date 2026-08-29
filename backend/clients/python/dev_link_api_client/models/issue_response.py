from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.issue_difficulty import IssueDifficulty
from ..models.issue_priority import IssuePriority
from ..models.issue_status import IssueStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="IssueResponse")


@_attrs_define
class IssueResponse:
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
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        issue_response = cls(
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
        )

        issue_response.additional_properties = d
        return issue_response

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
