from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.activity_response import ActivityResponse
    from ..models.announcement_response import AnnouncementResponse
    from ..models.dashboard_invitation import DashboardInvitation
    from ..models.dashboard_member import DashboardMember
    from ..models.milestone_response import MilestoneResponse


T = TypeVar("T", bound="ProjectDashboardResponse")


@_attrs_define
class ProjectDashboardResponse:
    """
    Attributes:
        project_id (UUID):
        title (str):
        stage (str):
        recent_activity (list[ActivityResponse]):
        milestones (list[MilestoneResponse]):
        announcements (list[AnnouncementResponse]):
        members (list[DashboardMember]):
        pending_invitations (list[DashboardInvitation]):
    """

    project_id: UUID
    title: str
    stage: str
    recent_activity: list[ActivityResponse]
    milestones: list[MilestoneResponse]
    announcements: list[AnnouncementResponse]
    members: list[DashboardMember]
    pending_invitations: list[DashboardInvitation]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project_id = str(self.project_id)

        title = self.title

        stage = self.stage

        recent_activity = []
        for recent_activity_item_data in self.recent_activity:
            recent_activity_item = recent_activity_item_data.to_dict()
            recent_activity.append(recent_activity_item)

        milestones = []
        for milestones_item_data in self.milestones:
            milestones_item = milestones_item_data.to_dict()
            milestones.append(milestones_item)

        announcements = []
        for announcements_item_data in self.announcements:
            announcements_item = announcements_item_data.to_dict()
            announcements.append(announcements_item)

        members = []
        for members_item_data in self.members:
            members_item = members_item_data.to_dict()
            members.append(members_item)

        pending_invitations = []
        for pending_invitations_item_data in self.pending_invitations:
            pending_invitations_item = pending_invitations_item_data.to_dict()
            pending_invitations.append(pending_invitations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project_id": project_id,
                "title": title,
                "stage": stage,
                "recent_activity": recent_activity,
                "milestones": milestones,
                "announcements": announcements,
                "members": members,
                "pending_invitations": pending_invitations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.activity_response import ActivityResponse
        from ..models.announcement_response import AnnouncementResponse
        from ..models.dashboard_invitation import DashboardInvitation
        from ..models.dashboard_member import DashboardMember
        from ..models.milestone_response import MilestoneResponse

        d = dict(src_dict)
        project_id = UUID(d.pop("project_id"))

        title = d.pop("title")

        stage = d.pop("stage")

        recent_activity = []
        _recent_activity = d.pop("recent_activity")
        for recent_activity_item_data in _recent_activity:
            recent_activity_item = ActivityResponse.from_dict(recent_activity_item_data)

            recent_activity.append(recent_activity_item)

        milestones = []
        _milestones = d.pop("milestones")
        for milestones_item_data in _milestones:
            milestones_item = MilestoneResponse.from_dict(milestones_item_data)

            milestones.append(milestones_item)

        announcements = []
        _announcements = d.pop("announcements")
        for announcements_item_data in _announcements:
            announcements_item = AnnouncementResponse.from_dict(announcements_item_data)

            announcements.append(announcements_item)

        members = []
        _members = d.pop("members")
        for members_item_data in _members:
            members_item = DashboardMember.from_dict(members_item_data)

            members.append(members_item)

        pending_invitations = []
        _pending_invitations = d.pop("pending_invitations")
        for pending_invitations_item_data in _pending_invitations:
            pending_invitations_item = DashboardInvitation.from_dict(
                pending_invitations_item_data
            )

            pending_invitations.append(pending_invitations_item)

        project_dashboard_response = cls(
            project_id=project_id,
            title=title,
            stage=stage,
            recent_activity=recent_activity,
            milestones=milestones,
            announcements=announcements,
            members=members,
            pending_invitations=pending_invitations,
        )

        project_dashboard_response.additional_properties = d
        return project_dashboard_response

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
