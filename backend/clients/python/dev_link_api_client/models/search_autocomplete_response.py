from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_suggestion_organization import SearchSuggestionOrganization
    from ..models.search_suggestion_project import SearchSuggestionProject
    from ..models.search_suggestion_skill import SearchSuggestionSkill
    from ..models.search_suggestion_tag import SearchSuggestionTag
    from ..models.search_suggestion_user import SearchSuggestionUser


T = TypeVar("T", bound="SearchAutocompleteResponse")


@_attrs_define
class SearchAutocompleteResponse:
    """
    Attributes:
        users (list[SearchSuggestionUser] | Unset):
        projects (list[SearchSuggestionProject] | Unset):
        organizations (list[SearchSuggestionOrganization] | Unset):
        skills (list[SearchSuggestionSkill] | Unset):
        tags (list[SearchSuggestionTag] | Unset):
    """

    users: list[SearchSuggestionUser] | Unset = UNSET
    projects: list[SearchSuggestionProject] | Unset = UNSET
    organizations: list[SearchSuggestionOrganization] | Unset = UNSET
    skills: list[SearchSuggestionSkill] | Unset = UNSET
    tags: list[SearchSuggestionTag] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        users: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.users, Unset):
            users = []
            for users_item_data in self.users:
                users_item = users_item_data.to_dict()
                users.append(users_item)

        projects: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.projects, Unset):
            projects = []
            for projects_item_data in self.projects:
                projects_item = projects_item_data.to_dict()
                projects.append(projects_item)

        organizations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.organizations, Unset):
            organizations = []
            for organizations_item_data in self.organizations:
                organizations_item = organizations_item_data.to_dict()
                organizations.append(organizations_item)

        skills: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.skills, Unset):
            skills = []
            for skills_item_data in self.skills:
                skills_item = skills_item_data.to_dict()
                skills.append(skills_item)

        tags: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = []
            for tags_item_data in self.tags:
                tags_item = tags_item_data.to_dict()
                tags.append(tags_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if users is not UNSET:
            field_dict["users"] = users
        if projects is not UNSET:
            field_dict["projects"] = projects
        if organizations is not UNSET:
            field_dict["organizations"] = organizations
        if skills is not UNSET:
            field_dict["skills"] = skills
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_suggestion_organization import SearchSuggestionOrganization
        from ..models.search_suggestion_project import SearchSuggestionProject
        from ..models.search_suggestion_skill import SearchSuggestionSkill
        from ..models.search_suggestion_tag import SearchSuggestionTag
        from ..models.search_suggestion_user import SearchSuggestionUser

        d = dict(src_dict)
        _users = d.pop("users", UNSET)
        users: list[SearchSuggestionUser] | Unset = UNSET
        if _users is not UNSET:
            users = []
            for users_item_data in _users:
                users_item = SearchSuggestionUser.from_dict(users_item_data)

                users.append(users_item)

        _projects = d.pop("projects", UNSET)
        projects: list[SearchSuggestionProject] | Unset = UNSET
        if _projects is not UNSET:
            projects = []
            for projects_item_data in _projects:
                projects_item = SearchSuggestionProject.from_dict(projects_item_data)

                projects.append(projects_item)

        _organizations = d.pop("organizations", UNSET)
        organizations: list[SearchSuggestionOrganization] | Unset = UNSET
        if _organizations is not UNSET:
            organizations = []
            for organizations_item_data in _organizations:
                organizations_item = SearchSuggestionOrganization.from_dict(
                    organizations_item_data
                )

                organizations.append(organizations_item)

        _skills = d.pop("skills", UNSET)
        skills: list[SearchSuggestionSkill] | Unset = UNSET
        if _skills is not UNSET:
            skills = []
            for skills_item_data in _skills:
                skills_item = SearchSuggestionSkill.from_dict(skills_item_data)

                skills.append(skills_item)

        _tags = d.pop("tags", UNSET)
        tags: list[SearchSuggestionTag] | Unset = UNSET
        if _tags is not UNSET:
            tags = []
            for tags_item_data in _tags:
                tags_item = SearchSuggestionTag.from_dict(tags_item_data)

                tags.append(tags_item)

        search_autocomplete_response = cls(
            users=users,
            projects=projects,
            organizations=organizations,
            skills=skills,
            tags=tags,
        )

        search_autocomplete_response.additional_properties = d
        return search_autocomplete_response

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
