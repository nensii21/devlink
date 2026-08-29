from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_org_audit_log_request_metadata_info_type_0 import (
        CreateOrgAuditLogRequestMetadataInfoType0,
    )


T = TypeVar("T", bound="CreateOrgAuditLogRequest")


@_attrs_define
class CreateOrgAuditLogRequest:
    """
    Attributes:
        action (str): Audit action e.g. member_invited, role_updated, project_created, settings_changed
        target_user_id (None | str | Unset):
        entity_type (str | Unset):  Default: 'organization'.
        entity_id (None | str | Unset):
        description (None | str | Unset):
        metadata_info (CreateOrgAuditLogRequestMetadataInfoType0 | None | Unset):
    """

    action: str
    target_user_id: None | str | Unset = UNSET
    entity_type: str | Unset = "organization"
    entity_id: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    metadata_info: CreateOrgAuditLogRequestMetadataInfoType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_org_audit_log_request_metadata_info_type_0 import (
            CreateOrgAuditLogRequestMetadataInfoType0,
        )

        action = self.action

        target_user_id: None | str | Unset
        if isinstance(self.target_user_id, Unset):
            target_user_id = UNSET
        else:
            target_user_id = self.target_user_id

        entity_type = self.entity_type

        entity_id: None | str | Unset
        if isinstance(self.entity_id, Unset):
            entity_id = UNSET
        else:
            entity_id = self.entity_id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        metadata_info: dict[str, Any] | None | Unset
        if isinstance(self.metadata_info, Unset):
            metadata_info = UNSET
        elif isinstance(self.metadata_info, CreateOrgAuditLogRequestMetadataInfoType0):
            metadata_info = self.metadata_info.to_dict()
        else:
            metadata_info = self.metadata_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
            }
        )
        if target_user_id is not UNSET:
            field_dict["target_user_id"] = target_user_id
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if entity_id is not UNSET:
            field_dict["entity_id"] = entity_id
        if description is not UNSET:
            field_dict["description"] = description
        if metadata_info is not UNSET:
            field_dict["metadata_info"] = metadata_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_org_audit_log_request_metadata_info_type_0 import (
            CreateOrgAuditLogRequestMetadataInfoType0,
        )

        d = dict(src_dict)
        action = d.pop("action")

        def _parse_target_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target_user_id = _parse_target_user_id(d.pop("target_user_id", UNSET))

        entity_type = d.pop("entity_type", UNSET)

        def _parse_entity_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        entity_id = _parse_entity_id(d.pop("entity_id", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_metadata_info(
            data: object,
        ) -> CreateOrgAuditLogRequestMetadataInfoType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_info_type_0 = (
                    CreateOrgAuditLogRequestMetadataInfoType0.from_dict(data)
                )

                return metadata_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateOrgAuditLogRequestMetadataInfoType0 | None | Unset, data)

        metadata_info = _parse_metadata_info(d.pop("metadata_info", UNSET))

        create_org_audit_log_request = cls(
            action=action,
            target_user_id=target_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata_info=metadata_info,
        )

        create_org_audit_log_request.additional_properties = d
        return create_org_audit_log_request

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
