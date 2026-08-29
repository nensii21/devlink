from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.project_stage import ProjectStage
from ..models.project_visibility import ProjectVisibility
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectUpdate")


@_attrs_define
class ProjectUpdate:
    """
    Attributes:
        title (None | str | Unset):
        slug (None | str | Unset):
        tagline (None | str | Unset):
        description (None | str | Unset):
        stage (None | ProjectStage | Unset):
        visibility (None | ProjectVisibility | Unset):
        tech_stack (None | str | Unset):
        repository_url (None | str | Unset):
        website_url (None | str | Unset):
        demo_url (None | str | Unset):
        team_size (int | None | Unset):
        max_team_size (int | None | Unset):
        hiring (bool | None | Unset):
        logo_url (None | str | Unset):
        banner_url (None | str | Unset):
        language (None | str | Unset):
        experience_level (None | str | Unset):
        is_remote (bool | None | Unset):
        is_paid (bool | None | Unset):
        is_opensource (bool | None | Unset):
        scheduled_publish_at (datetime.datetime | None | Unset):
        is_published (bool | None | Unset):
    """

    title: None | str | Unset = UNSET
    slug: None | str | Unset = UNSET
    tagline: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    stage: None | ProjectStage | Unset = UNSET
    visibility: None | ProjectVisibility | Unset = UNSET
    tech_stack: None | str | Unset = UNSET
    repository_url: None | str | Unset = UNSET
    website_url: None | str | Unset = UNSET
    demo_url: None | str | Unset = UNSET
    team_size: int | None | Unset = UNSET
    max_team_size: int | None | Unset = UNSET
    hiring: bool | None | Unset = UNSET
    logo_url: None | str | Unset = UNSET
    banner_url: None | str | Unset = UNSET
    language: None | str | Unset = UNSET
    experience_level: None | str | Unset = UNSET
    is_remote: bool | None | Unset = UNSET
    is_paid: bool | None | Unset = UNSET
    is_opensource: bool | None | Unset = UNSET
    scheduled_publish_at: datetime.datetime | None | Unset = UNSET
    is_published: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

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

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        stage: None | str | Unset
        if isinstance(self.stage, Unset):
            stage = UNSET
        elif isinstance(self.stage, ProjectStage):
            stage = self.stage.value
        else:
            stage = self.stage

        visibility: None | str | Unset
        if isinstance(self.visibility, Unset):
            visibility = UNSET
        elif isinstance(self.visibility, ProjectVisibility):
            visibility = self.visibility.value
        else:
            visibility = self.visibility

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

        team_size: int | None | Unset
        if isinstance(self.team_size, Unset):
            team_size = UNSET
        else:
            team_size = self.team_size

        max_team_size: int | None | Unset
        if isinstance(self.max_team_size, Unset):
            max_team_size = UNSET
        else:
            max_team_size = self.max_team_size

        hiring: bool | None | Unset
        if isinstance(self.hiring, Unset):
            hiring = UNSET
        else:
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

        is_remote: bool | None | Unset
        if isinstance(self.is_remote, Unset):
            is_remote = UNSET
        else:
            is_remote = self.is_remote

        is_paid: bool | None | Unset
        if isinstance(self.is_paid, Unset):
            is_paid = UNSET
        else:
            is_paid = self.is_paid

        is_opensource: bool | None | Unset
        if isinstance(self.is_opensource, Unset):
            is_opensource = UNSET
        else:
            is_opensource = self.is_opensource

        scheduled_publish_at: None | str | Unset
        if isinstance(self.scheduled_publish_at, Unset):
            scheduled_publish_at = UNSET
        elif isinstance(self.scheduled_publish_at, datetime.datetime):
            scheduled_publish_at = self.scheduled_publish_at.isoformat()
        else:
            scheduled_publish_at = self.scheduled_publish_at

        is_published: bool | None | Unset
        if isinstance(self.is_published, Unset):
            is_published = UNSET
        else:
            is_published = self.is_published

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if title is not UNSET:
            field_dict["title"] = title
        if slug is not UNSET:
            field_dict["slug"] = slug
        if tagline is not UNSET:
            field_dict["tagline"] = tagline
        if description is not UNSET:
            field_dict["description"] = description
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

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

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_stage(data: object) -> None | ProjectStage | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                stage_type_0 = ProjectStage(data)

                return stage_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectStage | Unset, data)

        stage = _parse_stage(d.pop("stage", UNSET))

        def _parse_visibility(data: object) -> None | ProjectVisibility | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                visibility_type_0 = ProjectVisibility(data)

                return visibility_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectVisibility | Unset, data)

        visibility = _parse_visibility(d.pop("visibility", UNSET))

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

        def _parse_team_size(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        team_size = _parse_team_size(d.pop("team_size", UNSET))

        def _parse_max_team_size(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_team_size = _parse_max_team_size(d.pop("max_team_size", UNSET))

        def _parse_hiring(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        hiring = _parse_hiring(d.pop("hiring", UNSET))

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

        def _parse_is_remote(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_remote = _parse_is_remote(d.pop("is_remote", UNSET))

        def _parse_is_paid(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_paid = _parse_is_paid(d.pop("is_paid", UNSET))

        def _parse_is_opensource(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_opensource = _parse_is_opensource(d.pop("is_opensource", UNSET))

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

        def _parse_is_published(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_published = _parse_is_published(d.pop("is_published", UNSET))

        project_update = cls(
            title=title,
            slug=slug,
            tagline=tagline,
            description=description,
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
        )

        project_update.additional_properties = d
        return project_update

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
