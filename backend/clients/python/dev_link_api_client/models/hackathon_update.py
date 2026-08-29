from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HackathonUpdate")


@_attrs_define
class HackathonUpdate:
    """
    Attributes:
        name (None | str | Unset):
        description (None | str | Unset):
        theme (None | str | Unset):
        registration_starts_at (datetime.datetime | None | Unset):
        registration_ends_at (datetime.datetime | None | Unset):
        starts_at (datetime.datetime | None | Unset):
        ends_at (datetime.datetime | None | Unset):
        min_team_size (int | None | Unset):
        max_team_size (int | None | Unset):
        prize (None | str | Unset):
        website_url (None | str | Unset):
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    theme: None | str | Unset = UNSET
    registration_starts_at: datetime.datetime | None | Unset = UNSET
    registration_ends_at: datetime.datetime | None | Unset = UNSET
    starts_at: datetime.datetime | None | Unset = UNSET
    ends_at: datetime.datetime | None | Unset = UNSET
    min_team_size: int | None | Unset = UNSET
    max_team_size: int | None | Unset = UNSET
    prize: None | str | Unset = UNSET
    website_url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        theme: None | str | Unset
        if isinstance(self.theme, Unset):
            theme = UNSET
        else:
            theme = self.theme

        registration_starts_at: None | str | Unset
        if isinstance(self.registration_starts_at, Unset):
            registration_starts_at = UNSET
        elif isinstance(self.registration_starts_at, datetime.datetime):
            registration_starts_at = self.registration_starts_at.isoformat()
        else:
            registration_starts_at = self.registration_starts_at

        registration_ends_at: None | str | Unset
        if isinstance(self.registration_ends_at, Unset):
            registration_ends_at = UNSET
        elif isinstance(self.registration_ends_at, datetime.datetime):
            registration_ends_at = self.registration_ends_at.isoformat()
        else:
            registration_ends_at = self.registration_ends_at

        starts_at: None | str | Unset
        if isinstance(self.starts_at, Unset):
            starts_at = UNSET
        elif isinstance(self.starts_at, datetime.datetime):
            starts_at = self.starts_at.isoformat()
        else:
            starts_at = self.starts_at

        ends_at: None | str | Unset
        if isinstance(self.ends_at, Unset):
            ends_at = UNSET
        elif isinstance(self.ends_at, datetime.datetime):
            ends_at = self.ends_at.isoformat()
        else:
            ends_at = self.ends_at

        min_team_size: int | None | Unset
        if isinstance(self.min_team_size, Unset):
            min_team_size = UNSET
        else:
            min_team_size = self.min_team_size

        max_team_size: int | None | Unset
        if isinstance(self.max_team_size, Unset):
            max_team_size = UNSET
        else:
            max_team_size = self.max_team_size

        prize: None | str | Unset
        if isinstance(self.prize, Unset):
            prize = UNSET
        else:
            prize = self.prize

        website_url: None | str | Unset
        if isinstance(self.website_url, Unset):
            website_url = UNSET
        else:
            website_url = self.website_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if theme is not UNSET:
            field_dict["theme"] = theme
        if registration_starts_at is not UNSET:
            field_dict["registration_starts_at"] = registration_starts_at
        if registration_ends_at is not UNSET:
            field_dict["registration_ends_at"] = registration_ends_at
        if starts_at is not UNSET:
            field_dict["starts_at"] = starts_at
        if ends_at is not UNSET:
            field_dict["ends_at"] = ends_at
        if min_team_size is not UNSET:
            field_dict["min_team_size"] = min_team_size
        if max_team_size is not UNSET:
            field_dict["max_team_size"] = max_team_size
        if prize is not UNSET:
            field_dict["prize"] = prize
        if website_url is not UNSET:
            field_dict["website_url"] = website_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_theme(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        theme = _parse_theme(d.pop("theme", UNSET))

        def _parse_registration_starts_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                registration_starts_at_type_0 = datetime.datetime.fromisoformat(data)

                return registration_starts_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        registration_starts_at = _parse_registration_starts_at(
            d.pop("registration_starts_at", UNSET)
        )

        def _parse_registration_ends_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                registration_ends_at_type_0 = datetime.datetime.fromisoformat(data)

                return registration_ends_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        registration_ends_at = _parse_registration_ends_at(
            d.pop("registration_ends_at", UNSET)
        )

        def _parse_starts_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                starts_at_type_0 = datetime.datetime.fromisoformat(data)

                return starts_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        starts_at = _parse_starts_at(d.pop("starts_at", UNSET))

        def _parse_ends_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ends_at_type_0 = datetime.datetime.fromisoformat(data)

                return ends_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ends_at = _parse_ends_at(d.pop("ends_at", UNSET))

        def _parse_min_team_size(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        min_team_size = _parse_min_team_size(d.pop("min_team_size", UNSET))

        def _parse_max_team_size(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_team_size = _parse_max_team_size(d.pop("max_team_size", UNSET))

        def _parse_prize(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        prize = _parse_prize(d.pop("prize", UNSET))

        def _parse_website_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        website_url = _parse_website_url(d.pop("website_url", UNSET))

        hackathon_update = cls(
            name=name,
            description=description,
            theme=theme,
            registration_starts_at=registration_starts_at,
            registration_ends_at=registration_ends_at,
            starts_at=starts_at,
            ends_at=ends_at,
            min_team_size=min_team_size,
            max_team_size=max_team_size,
            prize=prize,
            website_url=website_url,
        )

        hackathon_update.additional_properties = d
        return hackathon_update

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
