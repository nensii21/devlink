from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.project_stage import ProjectStage
from ..models.project_visibility import ProjectVisibility
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectResponse")


@_attrs_define
class ProjectResponse:
    """
    Attributes:
        title (str):
        description (str):
        id (UUID):
        owner_id (UUID):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        slug (None | str | Unset):
        tagline (None | str | Unset):
        stage (ProjectStage | Unset):
        visibility (ProjectVisibility | Unset):
        tech_stack (None | str | Unset):
        repository_url (None | str | Unset):
        website_url (None | str | Unset):
        demo_url (None | str | Unset):
        team_size (int | Unset):  Default: 1.
        max_team_size (int | Unset):  Default: 5.
        hiring (bool | Unset):  Default: True.
        logo_url (None | str | Unset):
        banner_url (None | str | Unset):
        language (None | str | Unset):
        experience_level (None | str | Unset):
        is_remote (bool | Unset):  Default: False.
        is_paid (bool | Unset):  Default: False.
        is_opensource (bool | Unset):  Default: False.
        scheduled_publish_at (datetime.datetime | None | Unset):
        is_published (bool | Unset):  Default: True.
        stars (int | Unset):  Default: 0.
        views (int | Unset):  Default: 0.
        applications_count (int | Unset):  Default: 0.
        is_featured (bool | Unset):  Default: False.
        is_archived (bool | Unset):  Default: False.
        deleted_at (datetime.datetime | None | Unset):
        deleted_by_id (None | Unset | UUID):
    """

    title: str
    description: str
    id: UUID
    owner_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    slug: None | str | Unset = UNSET
    tagline: None | str | Unset = UNSET
    stage: ProjectStage | Unset = UNSET
    visibility: ProjectVisibility | Unset = UNSET
    tech_stack: None | str | Unset = UNSET
    repository_url: None | str | Unset = UNSET
    website_url: None | str | Unset = UNSET
    demo_url: None | str | Unset = UNSET
    team_size: int | Unset = 1
    max_team_size: int | Unset = 5
    hiring: bool | Unset = True
    logo_url: None | str | Unset = UNSET
    banner_url: None | str | Unset = UNSET
    language: None | str | Unset = UNSET
    experience_level: None | str | Unset = UNSET
    is_remote: bool | Unset = False
    is_paid: bool | Unset = False
    is_opensource: bool | Unset = False
    scheduled_publish_at: datetime.datetime | None | Unset = UNSET
    is_published: bool | Unset = True
    stars: int | Unset = 0
    views: int | Unset = 0
    applications_count: int | Unset = 0
    is_featured: bool | Unset = False
    is_archived: bool | Unset = False
    deleted_at: datetime.datetime | None | Unset = UNSET
    deleted_by_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title

        description = self.description

        id = str(self.id)

        owner_id = str(self.owner_id)

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        slug: None | str | Unset
        if isinstance(self.slug, Unset):
            slug = UNSET
        else:
            slug = self.slug

        tagline: None | str | Unset
        if isinstance(self.tagline, Unset):
            tagline = UNSET
        else:
            tagline = self.tagline

        stage: str | Unset = UNSET
        if not isinstance(self.stage, Unset):
            stage = self.stage.value

        visibility: str | Unset = UNSET
        if not isinstance(self.visibility, Unset):
            visibility = self.visibility.value

        tech_stack: None | str | Unset
        if isinstance(self.tech_stack, Unset):
            tech_stack = UNSET
        else:
            tech_stack = self.tech_stack

        repository_url: None | str | Unset
        if isinstance(self.repository_url, Unset):
            repository_url = UNSET
        else:
            repository_url = self.repository_url

        website_url: None | str | Unset
        if isinstance(self.website_url, Unset):
            website_url = UNSET
        else:
            website_url = self.website_url

        demo_url: None | str | Unset
        if isinstance(self.demo_url, Unset):
            demo_url = UNSET
        else:
            demo_url = self.demo_url

        team_size = self.team_size

        max_team_size = self.max_team_size

        hiring = self.hiring

        logo_url: None | str | Unset
        if isinstance(self.logo_url, Unset):
            logo_url = UNSET
        else:
            logo_url = self.logo_url

        banner_url: None | str | Unset
        if isinstance(self.banner_url, Unset):
            banner_url = UNSET
        else:
            banner_url = self.banner_url

        language: None | str | Unset
        if isinstance(self.language, Unset):
            language = UNSET
        else:
            language = self.language

        experience_level: None | str | Unset
        if isinstance(self.experience_level, Unset):
            experience_level = UNSET
        else:
            experience_level = self.experience_level

        is_remote = self.is_remote

        is_paid = self.is_paid

        is_opensource = self.is_opensource

        scheduled_publish_at: None | str | Unset
        if isinstance(self.scheduled_publish_at, Unset):
            scheduled_publish_at = UNSET
        elif isinstance(self.scheduled_publish_at, datetime.datetime):
            scheduled_publish_at = self.scheduled_publish_at.isoformat()
        else:
            scheduled_publish_at = self.scheduled_publish_at

        is_published = self.is_published

        stars = self.stars

        views = self.views

        applications_count = self.applications_count

        is_featured = self.is_featured

        is_archived = self.is_archived

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        deleted_by_id: None | str | Unset
        if isinstance(self.deleted_by_id, Unset):
            deleted_by_id = UNSET
        elif isinstance(self.deleted_by_id, UUID):
            deleted_by_id = str(self.deleted_by_id)
        else:
            deleted_by_id = self.deleted_by_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "description": description,
                "id": id,
                "owner_id": owner_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if tagline is not UNSET:
            field_dict["tagline"] = tagline
        if stage is not UNSET:
            field_dict["stage"] = stage
        if visibility is not UNSET:
            field_dict["visibility"] = visibility
        if tech_stack is not UNSET:
            field_dict["tech_stack"] = tech_stack
        if repository_url is not UNSET:
            field_dict["repository_url"] = repository_url
        if website_url is not UNSET:
            field_dict["website_url"] = website_url
        if demo_url is not UNSET:
            field_dict["demo_url"] = demo_url
        if team_size is not UNSET:
            field_dict["team_size"] = team_size
        if max_team_size is not UNSET:
            field_dict["max_team_size"] = max_team_size
        if hiring is not UNSET:
            field_dict["hiring"] = hiring
        if logo_url is not UNSET:
            field_dict["logo_url"] = logo_url
        if banner_url is not UNSET:
            field_dict["banner_url"] = banner_url
        if language is not UNSET:
            field_dict["language"] = language
        if experience_level is not UNSET:
            field_dict["experience_level"] = experience_level
        if is_remote is not UNSET:
            field_dict["is_remote"] = is_remote
        if is_paid is not UNSET:
            field_dict["is_paid"] = is_paid
        if is_opensource is not UNSET:
            field_dict["is_opensource"] = is_opensource
        if scheduled_publish_at is not UNSET:
            field_dict["scheduled_publish_at"] = scheduled_publish_at
        if is_published is not UNSET:
            field_dict["is_published"] = is_published
        if stars is not UNSET:
            field_dict["stars"] = stars
        if views is not UNSET:
            field_dict["views"] = views
        if applications_count is not UNSET:
            field_dict["applications_count"] = applications_count
        if is_featured is not UNSET:
            field_dict["is_featured"] = is_featured
        if is_archived is not UNSET:
            field_dict["is_archived"] = is_archived
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if deleted_by_id is not UNSET:
            field_dict["deleted_by_id"] = deleted_by_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        title = d.pop("title")

        description = d.pop("description")

        id = UUID(d.pop("id"))

        owner_id = UUID(d.pop("owner_id"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_slug(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        slug = _parse_slug(d.pop("slug", UNSET))

        def _parse_tagline(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tagline = _parse_tagline(d.pop("tagline", UNSET))

        _stage = d.pop("stage", UNSET)
        stage: ProjectStage | Unset
        if isinstance(_stage, Unset):
            stage = UNSET
        else:
            stage = ProjectStage(_stage)

        _visibility = d.pop("visibility", UNSET)
        visibility: ProjectVisibility | Unset
        if isinstance(_visibility, Unset):
            visibility = UNSET
        else:
            visibility = ProjectVisibility(_visibility)

        def _parse_tech_stack(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tech_stack = _parse_tech_stack(d.pop("tech_stack", UNSET))

        def _parse_repository_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        repository_url = _parse_repository_url(d.pop("repository_url", UNSET))

        def _parse_website_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        website_url = _parse_website_url(d.pop("website_url", UNSET))

        def _parse_demo_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        demo_url = _parse_demo_url(d.pop("demo_url", UNSET))

        team_size = d.pop("team_size", UNSET)

        max_team_size = d.pop("max_team_size", UNSET)

        hiring = d.pop("hiring", UNSET)

        def _parse_logo_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        logo_url = _parse_logo_url(d.pop("logo_url", UNSET))

        def _parse_banner_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        banner_url = _parse_banner_url(d.pop("banner_url", UNSET))

        def _parse_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        language = _parse_language(d.pop("language", UNSET))

        def _parse_experience_level(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        experience_level = _parse_experience_level(d.pop("experience_level", UNSET))

        is_remote = d.pop("is_remote", UNSET)

        is_paid = d.pop("is_paid", UNSET)

        is_opensource = d.pop("is_opensource", UNSET)

        def _parse_scheduled_publish_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                scheduled_publish_at_type_0 = datetime.datetime.fromisoformat(data)

                return scheduled_publish_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        scheduled_publish_at = _parse_scheduled_publish_at(
            d.pop("scheduled_publish_at", UNSET)
        )

        is_published = d.pop("is_published", UNSET)

        stars = d.pop("stars", UNSET)

        views = d.pop("views", UNSET)

        applications_count = d.pop("applications_count", UNSET)

        is_featured = d.pop("is_featured", UNSET)

        is_archived = d.pop("is_archived", UNSET)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = datetime.datetime.fromisoformat(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        def _parse_deleted_by_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_by_id_type_0 = UUID(data)

                return deleted_by_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        deleted_by_id = _parse_deleted_by_id(d.pop("deleted_by_id", UNSET))

        project_response = cls(
            title=title,
            description=description,
            id=id,
            owner_id=owner_id,
            created_at=created_at,
            updated_at=updated_at,
            slug=slug,
            tagline=tagline,
            stage=stage,
            visibility=visibility,
            tech_stack=tech_stack,
            repository_url=repository_url,
            website_url=website_url,
            demo_url=demo_url,
            team_size=team_size,
            max_team_size=max_team_size,
            hiring=hiring,
            logo_url=logo_url,
            banner_url=banner_url,
            language=language,
            experience_level=experience_level,
            is_remote=is_remote,
            is_paid=is_paid,
            is_opensource=is_opensource,
            scheduled_publish_at=scheduled_publish_at,
            is_published=is_published,
            stars=stars,
            views=views,
            applications_count=applications_count,
            is_featured=is_featured,
            is_archived=is_archived,
            deleted_at=deleted_at,
            deleted_by_id=deleted_by_id,
        )

        project_response.additional_properties = d
        return project_response

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
