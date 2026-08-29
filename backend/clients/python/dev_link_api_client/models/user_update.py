from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.availability_slot import AvailabilitySlot
    from ..models.privacy_settings_update import PrivacySettingsUpdate


T = TypeVar("T", bound="UserUpdate")


@_attrs_define
class UserUpdate:
    """
    Attributes:
        first_name (None | str | Unset):
        last_name (None | str | Unset):
        headline (None | str | Unset):
        bio (None | str | Unset):
        location (None | str | Unset):
        timezone (None | str | Unset):
        public_email (None | str | Unset):
        website (None | str | Unset):
        resume_url (None | str | Unset):
        portfolio_url (None | str | Unset):
        github_url (None | str | Unset):
        linkedin_url (None | str | Unset):
        role (None | str | Unset):
        experience_level (None | str | Unset):
        company (None | str | Unset):
        open_to_work (bool | None | Unset):
        is_private (bool | None | Unset):
        privacy_settings (None | PrivacySettingsUpdate | Unset):
        availability (list[AvailabilitySlot] | None | Unset):
    """

    first_name: None | str | Unset = UNSET
    last_name: None | str | Unset = UNSET
    headline: None | str | Unset = UNSET
    bio: None | str | Unset = UNSET
    location: None | str | Unset = UNSET
    timezone: None | str | Unset = UNSET
    public_email: None | str | Unset = UNSET
    website: None | str | Unset = UNSET
    resume_url: None | str | Unset = UNSET
    portfolio_url: None | str | Unset = UNSET
    github_url: None | str | Unset = UNSET
    linkedin_url: None | str | Unset = UNSET
    role: None | str | Unset = UNSET
    experience_level: None | str | Unset = UNSET
    company: None | str | Unset = UNSET
    open_to_work: bool | None | Unset = UNSET
    is_private: bool | None | Unset = UNSET
    privacy_settings: None | PrivacySettingsUpdate | Unset = UNSET
    availability: list[AvailabilitySlot] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.privacy_settings_update import PrivacySettingsUpdate

        first_name: None | str | Unset
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        last_name: None | str | Unset
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        headline: None | str | Unset
        if isinstance(self.headline, Unset):
            headline = UNSET
        else:
            headline = self.headline

        bio: None | str | Unset
        if isinstance(self.bio, Unset):
            bio = UNSET
        else:
            bio = self.bio

        location: None | str | Unset
        if isinstance(self.location, Unset):
            location = UNSET
        else:
            location = self.location

        timezone: None | str | Unset
        if isinstance(self.timezone, Unset):
            timezone = UNSET
        else:
            timezone = self.timezone

        public_email: None | str | Unset
        if isinstance(self.public_email, Unset):
            public_email = UNSET
        else:
            public_email = self.public_email

        website: None | str | Unset
        if isinstance(self.website, Unset):
            website = UNSET
        else:
            website = self.website

        resume_url: None | str | Unset
        if isinstance(self.resume_url, Unset):
            resume_url = UNSET
        else:
            resume_url = self.resume_url

        portfolio_url: None | str | Unset
        if isinstance(self.portfolio_url, Unset):
            portfolio_url = UNSET
        else:
            portfolio_url = self.portfolio_url

        github_url: None | str | Unset
        if isinstance(self.github_url, Unset):
            github_url = UNSET
        else:
            github_url = self.github_url

        linkedin_url: None | str | Unset
        if isinstance(self.linkedin_url, Unset):
            linkedin_url = UNSET
        else:
            linkedin_url = self.linkedin_url

        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        experience_level: None | str | Unset
        if isinstance(self.experience_level, Unset):
            experience_level = UNSET
        else:
            experience_level = self.experience_level

        company: None | str | Unset
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        open_to_work: bool | None | Unset
        if isinstance(self.open_to_work, Unset):
            open_to_work = UNSET
        else:
            open_to_work = self.open_to_work

        is_private: bool | None | Unset
        if isinstance(self.is_private, Unset):
            is_private = UNSET
        else:
            is_private = self.is_private

        privacy_settings: dict[str, Any] | None | Unset
        if isinstance(self.privacy_settings, Unset):
            privacy_settings = UNSET
        elif isinstance(self.privacy_settings, PrivacySettingsUpdate):
            privacy_settings = self.privacy_settings.to_dict()
        else:
            privacy_settings = self.privacy_settings

        availability: list[dict[str, Any]] | None | Unset
        if isinstance(self.availability, Unset):
            availability = UNSET
        elif isinstance(self.availability, list):
            availability = []
            for availability_type_0_item_data in self.availability:
                availability_type_0_item = availability_type_0_item_data.to_dict()
                availability.append(availability_type_0_item)

        else:
            availability = self.availability

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if headline is not UNSET:
            field_dict["headline"] = headline
        if bio is not UNSET:
            field_dict["bio"] = bio
        if location is not UNSET:
            field_dict["location"] = location
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if public_email is not UNSET:
            field_dict["public_email"] = public_email
        if website is not UNSET:
            field_dict["website"] = website
        if resume_url is not UNSET:
            field_dict["resume_url"] = resume_url
        if portfolio_url is not UNSET:
            field_dict["portfolio_url"] = portfolio_url
        if github_url is not UNSET:
            field_dict["github_url"] = github_url
        if linkedin_url is not UNSET:
            field_dict["linkedin_url"] = linkedin_url
        if role is not UNSET:
            field_dict["role"] = role
        if experience_level is not UNSET:
            field_dict["experience_level"] = experience_level
        if company is not UNSET:
            field_dict["company"] = company
        if open_to_work is not UNSET:
            field_dict["open_to_work"] = open_to_work
        if is_private is not UNSET:
            field_dict["is_private"] = is_private
        if privacy_settings is not UNSET:
            field_dict["privacy_settings"] = privacy_settings
        if availability is not UNSET:
            field_dict["availability"] = availability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.availability_slot import AvailabilitySlot
        from ..models.privacy_settings_update import PrivacySettingsUpdate

        d = dict(src_dict)

        def _parse_first_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_last_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_headline(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        headline = _parse_headline(d.pop("headline", UNSET))

        def _parse_bio(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bio = _parse_bio(d.pop("bio", UNSET))

        def _parse_location(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        location = _parse_location(d.pop("location", UNSET))

        def _parse_timezone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        timezone = _parse_timezone(d.pop("timezone", UNSET))

        def _parse_public_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        public_email = _parse_public_email(d.pop("public_email", UNSET))

        def _parse_website(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        website = _parse_website(d.pop("website", UNSET))

        def _parse_resume_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        resume_url = _parse_resume_url(d.pop("resume_url", UNSET))

        def _parse_portfolio_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        portfolio_url = _parse_portfolio_url(d.pop("portfolio_url", UNSET))

        def _parse_github_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        github_url = _parse_github_url(d.pop("github_url", UNSET))

        def _parse_linkedin_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        linkedin_url = _parse_linkedin_url(d.pop("linkedin_url", UNSET))

        def _parse_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        def _parse_experience_level(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        experience_level = _parse_experience_level(d.pop("experience_level", UNSET))

        def _parse_company(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_open_to_work(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        open_to_work = _parse_open_to_work(d.pop("open_to_work", UNSET))

        def _parse_is_private(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_private = _parse_is_private(d.pop("is_private", UNSET))

        def _parse_privacy_settings(
            data: object,
        ) -> None | PrivacySettingsUpdate | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                privacy_settings_type_0 = PrivacySettingsUpdate.from_dict(data)

                return privacy_settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PrivacySettingsUpdate | Unset, data)

        privacy_settings = _parse_privacy_settings(d.pop("privacy_settings", UNSET))

        def _parse_availability(data: object) -> list[AvailabilitySlot] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                availability_type_0 = []
                _availability_type_0 = data
                for availability_type_0_item_data in _availability_type_0:
                    availability_type_0_item = AvailabilitySlot.from_dict(
                        availability_type_0_item_data
                    )

                    availability_type_0.append(availability_type_0_item)

                return availability_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[AvailabilitySlot] | None | Unset, data)

        availability = _parse_availability(d.pop("availability", UNSET))

        user_update = cls(
            first_name=first_name,
            last_name=last_name,
            headline=headline,
            bio=bio,
            location=location,
            timezone=timezone,
            public_email=public_email,
            website=website,
            resume_url=resume_url,
            portfolio_url=portfolio_url,
            github_url=github_url,
            linkedin_url=linkedin_url,
            role=role,
            experience_level=experience_level,
            company=company,
            open_to_work=open_to_work,
            is_private=is_private,
            privacy_settings=privacy_settings,
            availability=availability,
        )

        user_update.additional_properties = d
        return user_update

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
