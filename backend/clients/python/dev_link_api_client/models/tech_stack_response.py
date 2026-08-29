from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tech_stack_recommendation import TechStackRecommendation


T = TypeVar("T", bound="TechStackResponse")


@_attrs_define
class TechStackResponse:
    """AI-generated tech stack recommendation response.

    Attributes:
        project_idea (str):
        recommendations (list[TechStackRecommendation]): Ranked list of recommended technologies.
        summary (None | str | Unset): Brief explanation of the overall stack strategy.
    """

    project_idea: str
    recommendations: list[TechStackRecommendation]
    summary: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_idea = self.project_idea

        recommendations = []
        for recommendations_item_data in self.recommendations:
            recommendations_item = recommendations_item_data.to_dict()
            recommendations.append(recommendations_item)

        summary: None | str | Unset
        if isinstance(self.summary, Unset):
            summary = UNSET
        else:
            summary = self.summary

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_idea": project_idea,
                "recommendations": recommendations,
            }
        )
        if summary is not UNSET:
            field_dict["summary"] = summary

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tech_stack_recommendation import TechStackRecommendation

        d = dict(src_dict)
        project_idea = d.pop("project_idea")

        recommendations = []
        _recommendations = d.pop("recommendations")
        for recommendations_item_data in _recommendations:
            recommendations_item = TechStackRecommendation.from_dict(
                recommendations_item_data
            )

            recommendations.append(recommendations_item)

        def _parse_summary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        summary = _parse_summary(d.pop("summary", UNSET))

        tech_stack_response = cls(
            project_idea=project_idea,
            recommendations=recommendations,
            summary=summary,
        )

        tech_stack_response.additional_properties = d
        return tech_stack_response

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
