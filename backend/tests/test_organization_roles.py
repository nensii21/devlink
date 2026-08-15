from app.services.organization_service import OrganizationService
from app.models.organization_member import OrgMemberRole


def test_can_manage_role_owner():
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.OWNER, OrgMemberRole.ADMIN, OrgMemberRole.MEMBER
        )
        == True
    )
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.OWNER, OrgMemberRole.OWNER, OrgMemberRole.ADMIN
        )
        == True
    )


def test_can_manage_role_admin():
    # Admin can change member to recruiter
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.ADMIN, OrgMemberRole.MEMBER, OrgMemberRole.RECRUITER
        )
        == True
    )

    # Admin CANNOT change owner's role
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.ADMIN, OrgMemberRole.OWNER, OrgMemberRole.ADMIN
        )
        == False
    )

    # Admin CANNOT promote to owner
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.ADMIN, OrgMemberRole.MEMBER, OrgMemberRole.OWNER
        )
        == False
    )


def test_can_manage_role_others():
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.RECRUITER, OrgMemberRole.MEMBER, OrgMemberRole.MAINTAINER
        )
        == False
    )
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.MAINTAINER, OrgMemberRole.MEMBER, OrgMemberRole.RECRUITER
        )
        == False
    )
    assert (
        OrganizationService.can_manage_role(
            OrgMemberRole.MEMBER, OrgMemberRole.MEMBER, OrgMemberRole.ADMIN
        )
        == False
    )
