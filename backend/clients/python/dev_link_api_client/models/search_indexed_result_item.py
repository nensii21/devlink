from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_indexed_result_item_metadata import (
        SearchIndexedResultItemMetadata,
    )


T = TypeVar("T", bound="SearchIndexedResultItem")


@_attrs_define
class SearchIndexedResultItem:
    """
    Attributes:
        id (str):
        entity_type (str):
        title (str):
        score (float):
        description (None | str | Unset):
        metadata (SearchIndexedResultItemMetadata | Unset):
    """

    id: str
    entity_type: str
    title: str
    score: float
    description: None | str | Unset = UNSET
    metadata: SearchIndexedResultItemMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        entity_type = self.entity_type

        title = self.title

        score = self.score

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "entity_type": entity_type,
                "title": title,
                "score": score,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_indexed_result_item_metadata import (
            SearchIndexedResultItemMetadata,
        )

        d = dict(src_dict)
        id = d.pop("id")

        entity_type = d.pop("entity_type")

        title = d.pop("title")

        score = d.pop("score")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: SearchIndexedResultItemMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = SearchIndexedResultItemMetadata.from_dict(_metadata)

        search_indexed_result_item = cls(
            id=id,
            entity_type=entity_type,
            title=title,
            score=score,
            description=description,
            metadata=metadata,
        )

        search_indexed_result_item.additional_properties = d
        return search_indexed_result_item

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
