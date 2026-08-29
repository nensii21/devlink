from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.exported_application import ExportedApplication
    from ..models.exported_bookmark import ExportedBookmark
    from ..models.exported_connection import ExportedConnection
    from ..models.exported_message import ExportedMessage
    from ..models.exported_organization import ExportedOrganization
    from ..models.exported_project import ExportedProject
    from ..models.exported_skill import ExportedSkill
    from ..models.user_export_data_activities_item import UserExportDataActivitiesItem
    from ..models.user_export_data_builder_flares_item import (
        UserExportDataBuilderFlaresItem,
    )
    from ..models.user_export_data_notifications_item import (
        UserExportDataNotificationsItem,
    )
    from ..models.user_export_data_profile import UserExportDataProfile
    from ..models.user_export_data_project_memberships_item import (
        UserExportDataProjectMembershipsItem,
    )


T = TypeVar("T", bound="UserExportData")


@_attrs_define
class UserExportData:
    """
    Attributes:
        exported_at (datetime.datetime):
        profile (UserExportDataProfile):
        skills (list[ExportedSkill]):
        projects (list[ExportedProject]):
        project_memberships (list[UserExportDataProjectMembershipsItem]):
        applications (list[ExportedApplication]):
        connections (list[ExportedConnection]):
        messages (list[ExportedMessage]):
        bookmarks (list[ExportedBookmark]):
        organizations (list[ExportedOrganization]):
        activities (list[UserExportDataActivitiesItem]):
        notifications (list[UserExportDataNotificationsItem]):
        builder_flares (list[UserExportDataBuilderFlaresItem]):
    """

    exported_at: datetime.datetime
    profile: UserExportDataProfile
    skills: list[ExportedSkill]
    projects: list[ExportedProject]
    project_memberships: list[UserExportDataProjectMembershipsItem]
    applications: list[ExportedApplication]
    connections: list[ExportedConnection]
    messages: list[ExportedMessage]
    bookmarks: list[ExportedBookmark]
    organizations: list[ExportedOrganization]
    activities: list[UserExportDataActivitiesItem]
    notifications: list[UserExportDataNotificationsItem]
    builder_flares: list[UserExportDataBuilderFlaresItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exported_at = self.exported_at.isoformat()

        profile = self.profile.to_dict()

        skills = []
        for skills_item_data in self.skills:
            skills_item = skills_item_data.to_dict()
            skills.append(skills_item)

        projects = []
        for projects_item_data in self.projects:
            projects_item = projects_item_data.to_dict()
            projects.append(projects_item)

        project_memberships = []
        for project_memberships_item_data in self.project_memberships:
            project_memberships_item = project_memberships_item_data.to_dict()
            project_memberships.append(project_memberships_item)

        applications = []
        for applications_item_data in self.applications:
            applications_item = applications_item_data.to_dict()
            applications.append(applications_item)

        connections = []
        for connections_item_data in self.connections:
            connections_item = connections_item_data.to_dict()
            connections.append(connections_item)

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        bookmarks = []
        for bookmarks_item_data in self.bookmarks:
            bookmarks_item = bookmarks_item_data.to_dict()
            bookmarks.append(bookmarks_item)

        organizations = []
        for organizations_item_data in self.organizations:
            organizations_item = organizations_item_data.to_dict()
            organizations.append(organizations_item)

        activities = []
        for activities_item_data in self.activities:
            activities_item = activities_item_data.to_dict()
            activities.append(activities_item)

        notifications = []
        for notifications_item_data in self.notifications:
            notifications_item = notifications_item_data.to_dict()
            notifications.append(notifications_item)

        builder_flares = []
        for builder_flares_item_data in self.builder_flares:
            builder_flares_item = builder_flares_item_data.to_dict()
            builder_flares.append(builder_flares_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "exported_at": exported_at,
                "profile": profile,
                "skills": skills,
                "projects": projects,
                "project_memberships": project_memberships,
                "applications": applications,
                "connections": connections,
                "messages": messages,
                "bookmarks": bookmarks,
                "organizations": organizations,
                "activities": activities,
                "notifications": notifications,
                "builder_flares": builder_flares,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.exported_application import ExportedApplication
        from ..models.exported_bookmark import ExportedBookmark
        from ..models.exported_connection import ExportedConnection
        from ..models.exported_message import ExportedMessage
        from ..models.exported_organization import ExportedOrganization
        from ..models.exported_project import ExportedProject
        from ..models.exported_skill import ExportedSkill
        from ..models.user_export_data_activities_item import (
            UserExportDataActivitiesItem,
        )
        from ..models.user_export_data_builder_flares_item import (
            UserExportDataBuilderFlaresItem,
        )
        from ..models.user_export_data_notifications_item import (
            UserExportDataNotificationsItem,
        )
        from ..models.user_export_data_profile import UserExportDataProfile
        from ..models.user_export_data_project_memberships_item import (
            UserExportDataProjectMembershipsItem,
        )

        d = dict(src_dict)
        exported_at = datetime.datetime.fromisoformat(d.pop("exported_at"))

        profile = UserExportDataProfile.from_dict(d.pop("profile"))

        skills = []
        _skills = d.pop("skills")
        for skills_item_data in _skills:
            skills_item = ExportedSkill.from_dict(skills_item_data)

            skills.append(skills_item)

        projects = []
        _projects = d.pop("projects")
        for projects_item_data in _projects:
            projects_item = ExportedProject.from_dict(projects_item_data)

            projects.append(projects_item)

        project_memberships = []
        _project_memberships = d.pop("project_memberships")
        for project_memberships_item_data in _project_memberships:
            project_memberships_item = UserExportDataProjectMembershipsItem.from_dict(
                project_memberships_item_data
            )

            project_memberships.append(project_memberships_item)

        applications = []
        _applications = d.pop("applications")
        for applications_item_data in _applications:
            applications_item = ExportedApplication.from_dict(applications_item_data)

            applications.append(applications_item)

        connections = []
        _connections = d.pop("connections")
        for connections_item_data in _connections:
            connections_item = ExportedConnection.from_dict(connections_item_data)

            connections.append(connections_item)

        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = ExportedMessage.from_dict(messages_item_data)

            messages.append(messages_item)

        bookmarks = []
        _bookmarks = d.pop("bookmarks")
        for bookmarks_item_data in _bookmarks:
            bookmarks_item = ExportedBookmark.from_dict(bookmarks_item_data)

            bookmarks.append(bookmarks_item)

        organizations = []
        _organizations = d.pop("organizations")
        for organizations_item_data in _organizations:
            organizations_item = ExportedOrganization.from_dict(organizations_item_data)

            organizations.append(organizations_item)

        activities = []
        _activities = d.pop("activities")
        for activities_item_data in _activities:
            activities_item = UserExportDataActivitiesItem.from_dict(
                activities_item_data
            )

            activities.append(activities_item)

        notifications = []
        _notifications = d.pop("notifications")
        for notifications_item_data in _notifications:
            notifications_item = UserExportDataNotificationsItem.from_dict(
                notifications_item_data
            )

            notifications.append(notifications_item)

        builder_flares = []
        _builder_flares = d.pop("builder_flares")
        for builder_flares_item_data in _builder_flares:
            builder_flares_item = UserExportDataBuilderFlaresItem.from_dict(
                builder_flares_item_data
            )

            builder_flares.append(builder_flares_item)

        user_export_data = cls(
            exported_at=exported_at,
            profile=profile,
            skills=skills,
            projects=projects,
            project_memberships=project_memberships,
            applications=applications,
            connections=connections,
            messages=messages,
            bookmarks=bookmarks,
            organizations=organizations,
            activities=activities,
            notifications=notifications,
            builder_flares=builder_flares,
        )

        user_export_data.additional_properties = d
        return user_export_data

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
