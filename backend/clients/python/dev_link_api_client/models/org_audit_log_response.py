from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.org_audit_log_response_metadata_info_type_0 import (
        OrgAuditLogResponseMetadataInfoType0,
    )


T = TypeVar("T", bound="OrgAuditLogResponse")


@_attrs_define
class OrgAuditLogResponse:
    """
    Attributes:
        id (str | UUID):
        organization_id (str | UUID):
        action (str):
        entity_type (str):
        created_at (datetime.datetime):
        actor_id (None | str | Unset | UUID):
        target_user_id (None | str | Unset | UUID):
        entity_id (None | str | Unset):
        description (None | str | Unset):
        ip_address (None | str | Unset):
        metadata_info (None | OrgAuditLogResponseMetadataInfoType0 | Unset):
    """

    id: str | UUID
    organization_id: str | UUID
    action: str
    entity_type: str
    created_at: datetime.datetime
    actor_id: None | str | Unset | UUID = UNSET
    target_user_id: None | str | Unset | UUID = UNSET
    entity_id: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    ip_address: None | str | Unset = UNSET
    metadata_info: None | OrgAuditLogResponseMetadataInfoType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.org_audit_log_response_metadata_info_type_0 import (
            OrgAuditLogResponseMetadataInfoType0,
        )

        id: str
        if isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        organization_id: str
        if isinstance(self.organization_id, UUID):
            organization_id = str(self.organization_id)
        else:
            organization_id = self.organization_id

        action = self.action

        entity_type = self.entity_type

        created_at = self.created_at.isoformat()

        actor_id: None | str | Unset
        if isinstance(self.actor_id, Unset):
            actor_id = UNSET
        elif isinstance(self.actor_id, UUID):
            actor_id = str(self.actor_id)
        else:
            actor_id = self.actor_id

        target_user_id: None | str | Unset
        if isinstance(self.target_user_id, Unset):
            target_user_id = UNSET
        elif isinstance(self.target_user_id, UUID):
            target_user_id = str(self.target_user_id)
        else:
            target_user_id = self.target_user_id

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

        ip_address: None | str | Unset
        if isinstance(self.ip_address, Unset):
            ip_address = UNSET
        else:
            ip_address = self.ip_address

        metadata_info: dict[str, Any] | None | Unset
        if isinstance(self.metadata_info, Unset):
            metadata_info = UNSET
        elif isinstance(self.metadata_info, OrgAuditLogResponseMetadataInfoType0):
            metadata_info = self.metadata_info.to_dict()
        else:
            metadata_info = self.metadata_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organization_id": organization_id,
                "action": action,
                "entity_type": entity_type,
                "created_at": created_at,
            }
        )
        if actor_id is not UNSET:
            field_dict["actor_id"] = actor_id
        if target_user_id is not UNSET:
            field_dict["target_user_id"] = target_user_id
        if entity_id is not UNSET:
            field_dict["entity_id"] = entity_id
        if description is not UNSET:
            field_dict["description"] = description
        if ip_address is not UNSET:
            field_dict["ip_address"] = ip_address
        if metadata_info is not UNSET:
            field_dict["metadata_info"] = metadata_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.org_audit_log_response_metadata_info_type_0 import (
            OrgAuditLogResponseMetadataInfoType0,
        )

        d = dict(src_dict)

        def _parse_id(data: object) -> str | UUID:
            try:
                if not isinstance(data, str):
                    raise TypeError()
                id_type_0 = UUID(data)

                return id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(str | UUID, data)

        id = _parse_id(d.pop("id"))

        def _parse_organization_id(data: object) -> str | UUID:
            try:
                if not isinstance(data, str):
                    raise TypeError()
                organization_id_type_0 = UUID(data)

                return organization_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(str | UUID, data)

        organization_id = _parse_organization_id(d.pop("organization_id"))

        action = d.pop("action")

        entity_type = d.pop("entity_type")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_actor_id(data: object) -> None | str | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                actor_id_type_0 = UUID(data)

                return actor_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | str | Unset | UUID, data)

        actor_id = _parse_actor_id(d.pop("actor_id", UNSET))

        def _parse_target_user_id(data: object) -> None | str | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                target_user_id_type_0 = UUID(data)

                return target_user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | str | Unset | UUID, data)

        target_user_id = _parse_target_user_id(d.pop("target_user_id", UNSET))

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

        def _parse_ip_address(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip_address = _parse_ip_address(d.pop("ip_address", UNSET))

        def _parse_metadata_info(
            data: object,
        ) -> None | OrgAuditLogResponseMetadataInfoType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_info_type_0 = OrgAuditLogResponseMetadataInfoType0.from_dict(
                    data
                )

                return metadata_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrgAuditLogResponseMetadataInfoType0 | Unset, data)

        metadata_info = _parse_metadata_info(d.pop("metadata_info", UNSET))

        org_audit_log_response = cls(
            id=id,
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            created_at=created_at,
            actor_id=actor_id,
            target_user_id=target_user_id,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address,
            metadata_info=metadata_info,
        )

        org_audit_log_response.additional_properties = d
        return org_audit_log_response

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
