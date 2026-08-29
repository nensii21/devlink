from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.audit_action import AuditAction

if TYPE_CHECKING:
    from ..models.audit_log_response_metadata_info_type_0 import (
        AuditLogResponseMetadataInfoType0,
    )
    from ..models.audit_log_response_new_values_type_0 import (
        AuditLogResponseNewValuesType0,
    )
    from ..models.audit_log_response_old_values_type_0 import (
        AuditLogResponseOldValuesType0,
    )


T = TypeVar("T", bound="AuditLogResponse")


@_attrs_define
class AuditLogResponse:
    """
    Attributes:
        id (UUID):
        actor_id (None | UUID):
        target_user_id (None | UUID):
        project_id (None | UUID):
        organization_id (None | UUID):
        action (AuditAction):
        entity_type (str):
        entity_id (None | str):
        description (None | str):
        old_values (AuditLogResponseOldValuesType0 | None):
        new_values (AuditLogResponseNewValuesType0 | None):
        metadata_info (AuditLogResponseMetadataInfoType0 | None):
        ip_address (None | str):
        user_agent (None | str):
        request_method (None | str):
        request_path (None | str):
        success (bool):
        status_code (int | None):
        error_message (None | str):
        created_at (datetime.datetime):
    """

    id: UUID
    actor_id: None | UUID
    target_user_id: None | UUID
    project_id: None | UUID
    organization_id: None | UUID
    action: AuditAction
    entity_type: str
    entity_id: None | str
    description: None | str
    old_values: AuditLogResponseOldValuesType0 | None
    new_values: AuditLogResponseNewValuesType0 | None
    metadata_info: AuditLogResponseMetadataInfoType0 | None
    ip_address: None | str
    user_agent: None | str
    request_method: None | str
    request_path: None | str
    success: bool
    status_code: int | None
    error_message: None | str
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.audit_log_response_metadata_info_type_0 import (
            AuditLogResponseMetadataInfoType0,
        )
        from ..models.audit_log_response_new_values_type_0 import (
            AuditLogResponseNewValuesType0,
        )
        from ..models.audit_log_response_old_values_type_0 import (
            AuditLogResponseOldValuesType0,
        )

        id = str(self.id)

        actor_id: None | str
        if isinstance(self.actor_id, UUID):
            actor_id = str(self.actor_id)
        else:
            actor_id = self.actor_id

        target_user_id: None | str
        if isinstance(self.target_user_id, UUID):
            target_user_id = str(self.target_user_id)
        else:
            target_user_id = self.target_user_id

        project_id: None | str
        if isinstance(self.project_id, UUID):
            project_id = str(self.project_id)
        else:
            project_id = self.project_id

        organization_id: None | str
        if isinstance(self.organization_id, UUID):
            organization_id = str(self.organization_id)
        else:
            organization_id = self.organization_id

        action = self.action.value

        entity_type = self.entity_type

        entity_id: None | str
        entity_id = self.entity_id

        description: None | str
        description = self.description

        old_values: dict[str, Any] | None
        if isinstance(self.old_values, AuditLogResponseOldValuesType0):
            old_values = self.old_values.to_dict()
        else:
            old_values = self.old_values

        new_values: dict[str, Any] | None
        if isinstance(self.new_values, AuditLogResponseNewValuesType0):
            new_values = self.new_values.to_dict()
        else:
            new_values = self.new_values

        metadata_info: dict[str, Any] | None
        if isinstance(self.metadata_info, AuditLogResponseMetadataInfoType0):
            metadata_info = self.metadata_info.to_dict()
        else:
            metadata_info = self.metadata_info

        ip_address: None | str
        ip_address = self.ip_address

        user_agent: None | str
        user_agent = self.user_agent

        request_method: None | str
        request_method = self.request_method

        request_path: None | str
        request_path = self.request_path

        success = self.success

        status_code: int | None
        status_code = self.status_code

        error_message: None | str
        error_message = self.error_message

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "actor_id": actor_id,
                "target_user_id": target_user_id,
                "project_id": project_id,
                "organization_id": organization_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "description": description,
                "old_values": old_values,
                "new_values": new_values,
                "metadata_info": metadata_info,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_method": request_method,
                "request_path": request_path,
                "success": success,
                "status_code": status_code,
                "error_message": error_message,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_response_metadata_info_type_0 import (
            AuditLogResponseMetadataInfoType0,
        )
        from ..models.audit_log_response_new_values_type_0 import (
            AuditLogResponseNewValuesType0,
        )
        from ..models.audit_log_response_old_values_type_0 import (
            AuditLogResponseOldValuesType0,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        def _parse_actor_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                actor_id_type_0 = UUID(data)

                return actor_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        actor_id = _parse_actor_id(d.pop("actor_id"))

        def _parse_target_user_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                target_user_id_type_0 = UUID(data)

                return target_user_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        target_user_id = _parse_target_user_id(d.pop("target_user_id"))

        def _parse_project_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                project_id_type_0 = UUID(data)

                return project_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        project_id = _parse_project_id(d.pop("project_id"))

        def _parse_organization_id(data: object) -> None | UUID:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                organization_id_type_0 = UUID(data)

                return organization_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | UUID, data)

        organization_id = _parse_organization_id(d.pop("organization_id"))

        action = AuditAction(d.pop("action"))

        entity_type = d.pop("entity_type")

        def _parse_entity_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        entity_id = _parse_entity_id(d.pop("entity_id"))

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        def _parse_old_values(data: object) -> AuditLogResponseOldValuesType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                old_values_type_0 = AuditLogResponseOldValuesType0.from_dict(data)

                return old_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AuditLogResponseOldValuesType0 | None, data)

        old_values = _parse_old_values(d.pop("old_values"))

        def _parse_new_values(data: object) -> AuditLogResponseNewValuesType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                new_values_type_0 = AuditLogResponseNewValuesType0.from_dict(data)

                return new_values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AuditLogResponseNewValuesType0 | None, data)

        new_values = _parse_new_values(d.pop("new_values"))

        def _parse_metadata_info(
            data: object,
        ) -> AuditLogResponseMetadataInfoType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_info_type_0 = AuditLogResponseMetadataInfoType0.from_dict(data)

                return metadata_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AuditLogResponseMetadataInfoType0 | None, data)

        metadata_info = _parse_metadata_info(d.pop("metadata_info"))

        def _parse_ip_address(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ip_address = _parse_ip_address(d.pop("ip_address"))

        def _parse_user_agent(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        user_agent = _parse_user_agent(d.pop("user_agent"))

        def _parse_request_method(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        request_method = _parse_request_method(d.pop("request_method"))

        def _parse_request_path(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        request_path = _parse_request_path(d.pop("request_path"))

        success = d.pop("success")

        def _parse_status_code(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        status_code = _parse_status_code(d.pop("status_code"))

        def _parse_error_message(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error_message = _parse_error_message(d.pop("error_message"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        audit_log_response = cls(
            id=id,
            actor_id=actor_id,
            target_user_id=target_user_id,
            project_id=project_id,
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata_info=metadata_info,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            success=success,
            status_code=status_code,
            error_message=error_message,
            created_at=created_at,
        )

        audit_log_response.additional_properties = d
        return audit_log_response

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
