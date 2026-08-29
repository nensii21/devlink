from __future__ import annotations

from typing import Any, Dict, List
from app.schemas.email_template import (
    EmailTemplateType,
    EmailRenderResponse,
    EmailTemplateInfo,
)


class EmailTemplateService:
    TEMPLATES_INFO: Dict[EmailTemplateType, Dict[str, Any]] = {
        EmailTemplateType.WELCOME: {
            "name": "Welcome Email",
            "description": "Sent to newly registered developers welcoming them to DevLink.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "action_url": "https://devlink.app/dashboard",
            },
        },
        EmailTemplateType.PASSWORD_RESET: {
            "name": "Password Reset",
            "description": "Transactional email containing password reset link and security instructions.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "reset_url": "https://devlink.app/reset-password?token=sample123",
                "expires_in_minutes": 30,
            },
        },
        EmailTemplateType.EMAIL_VERIFICATION: {
            "name": "Email Verification",
            "description": "Sent to verify developer email address upon sign up or email change.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "verify_url": "https://devlink.app/verify-email?code=987654",
            },
        },
        EmailTemplateType.TEAM_INVITATION: {
            "name": "Team Invitation",
            "description": "Invites a user to join a project team or organization.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "inviter_name": "Sarah Connor",
                "project_name": "AI Code Assistant",
                "invite_url": "https://devlink.app/invites/abc12345",
            },
        },
        EmailTemplateType.PROJECT_ACCEPTED: {
            "name": "Project Accepted",
            "description": "Notifies applicant that their application to a project team was accepted.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "project_name": "DevLink Open Source Engine",
                "role_title": "Fullstack Developer",
                "workspace_url": "https://devlink.app/projects/1",
            },
        },
        EmailTemplateType.PROJECT_REJECTED: {
            "name": "Project Application Status Update",
            "description": "Polite notification for applications that were not selected.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "project_name": "DevLink Open Source Engine",
                "feedback_url": "https://devlink.app/projects",
            },
        },
        EmailTemplateType.WEEKLY_DIGEST: {
            "name": "Weekly Developer Digest",
            "description": "Summary of developer recommendations, profile views, and team activity.",
            "sample_context": {
                "user_name": "Alex Mercer",
                "profile_views": 42,
                "new_matches": 5,
                "trending_projects": ["AI Code Reviewer", "Cloud Native Dashboard"],
                "digest_url": "https://devlink.app/digest",
            },
        },
    }

    @classmethod
    def list_templates(cls) -> List[EmailTemplateInfo]:
        results = []
        for t_type, info in cls.TEMPLATES_INFO.items():
            results.append(
                EmailTemplateInfo(
                    template_type=t_type,
                    name=info["name"],
                    description=info["description"],
                    sample_context=info["sample_context"],
                )
            )
        return results

    @classmethod
    def render_template(
        cls, template_type: EmailTemplateType, context: Dict[str, Any]
    ) -> EmailRenderResponse:
        info = cls.TEMPLATES_INFO.get(template_type, {})
        sample_ctx = info.get("sample_context", {})
        ctx = {**sample_ctx, **context}

        user_name = ctx.get("user_name", "Developer")

        if template_type == EmailTemplateType.WELCOME:
            subject = f"Welcome to DevLink, {user_name}! 🚀"
            body_content = f"""
                <h2>Welcome to DevLink, {user_name}!</h2>
                <p>We are thrilled to have you in our global developer community. Connect, collaborate on open-source projects, build your developer portfolio, and showcase your skills.</p>
                <p><a href="{ctx.get('action_url', '#')}" class="btn">Explore Dashboard</a></p>
            """
            plain_content = f"Welcome to DevLink, {user_name}!\n\nWe are thrilled to have you in our community. Explore your dashboard here: {ctx.get('action_url', '#')}"

        elif template_type == EmailTemplateType.PASSWORD_RESET:
            subject = "Reset Your DevLink Password 🔐"
            body_content = f"""
                <h2>Password Reset Request</h2>
                <p>Hello {user_name}, we received a request to reset your password. Click the button below within {ctx.get('expires_in_minutes', 30)} minutes to choose a new password.</p>
                <p><a href="{ctx.get('reset_url', '#')}" class="btn">Reset Password</a></p>
                <p><small>If you did not request this, please ignore this email.</small></p>
            """
            plain_content = f"Password Reset Request\n\nHello {user_name}, reset your password here: {ctx.get('reset_url', '#')}\nLink expires in {ctx.get('expires_in_minutes', 30)} minutes."

        elif template_type == EmailTemplateType.EMAIL_VERIFICATION:
            subject = "Verify Your DevLink Email Address ✉️"
            body_content = f"""
                <h2>Email Verification</h2>
                <p>Hello {user_name}, please confirm your email address to unlock all DevLink collaboration features.</p>
                <p><a href="{ctx.get('verify_url', '#')}" class="btn">Verify Email Address</a></p>
            """
            plain_content = f"Verify Your Email Address\n\nHello {user_name}, verify your email address here: {ctx.get('verify_url', '#')}"

        elif template_type == EmailTemplateType.TEAM_INVITATION:
            subject = f"{ctx.get('inviter_name', 'A teammate')} invited you to join '{ctx.get('project_name', 'a project')}'"
            body_content = f"""
                <h2>You're Invited!</h2>
                <p>Hello {user_name}, <strong>{ctx.get('inviter_name', 'A team member')}</strong> has invited you to join the project team for <strong>{ctx.get('project_name', 'a project')}</strong>.</p>
                <p><a href="{ctx.get('invite_url', '#')}" class="btn">Accept Invitation</a></p>
            """
            plain_content = f"You're Invited!\n\nHello {user_name}, {ctx.get('inviter_name')} invited you to join '{ctx.get('project_name')}'. Accept here: {ctx.get('invite_url', '#')}"

        elif template_type == EmailTemplateType.PROJECT_ACCEPTED:
            subject = f"Application Accepted: Welcome to '{ctx.get('project_name')}' 🎉"
            body_content = f"""
                <h2>Application Accepted!</h2>
                <p>Great news {user_name}! Your application for the role of <strong>{ctx.get('role_title', 'Contributor')}</strong> on <strong>{ctx.get('project_name')}</strong> has been accepted.</p>
                <p><a href="{ctx.get('workspace_url', '#')}" class="btn">Go to Project Workspace</a></p>
            """
            plain_content = f"Application Accepted!\n\nCongratulations {user_name}! You were accepted for '{ctx.get('project_name')}' as {ctx.get('role_title')}. Access project: {ctx.get('workspace_url', '#')}"

        elif template_type == EmailTemplateType.PROJECT_REJECTED:
            subject = (
                f"Update regarding your application for '{ctx.get('project_name')}'"
            )
            body_content = f"""
                <h2>Application Status Update</h2>
                <p>Hello {user_name}, thank you for your interest in <strong>{ctx.get('project_name')}</strong>. Although your profile was impressive, the team chose to proceed with another applicant for this specific role.</p>
                <p><a href="{ctx.get('feedback_url', '#')}" class="btn">Browse Other Projects</a></p>
            """
            plain_content = f"Application Status Update\n\nHello {user_name}, thank you for applying to '{ctx.get('project_name')}'. Browse other open opportunities: {ctx.get('feedback_url', '#')}"

        else:  # WEEKLY_DIGEST
            subject = f"Your DevLink Weekly Digest ({ctx.get('profile_views', 0)} Profile Views) 📈"
            projects_list = "".join(
                [f"<li>{p}</li>" for p in ctx.get("trending_projects", [])]
            )
            body_content = f"""
                <h2>Weekly Digest for {user_name}</h2>
                <p>Here is your weekly collaboration summary:</p>
                <ul>
                    <li><strong>Profile Views:</strong> {ctx.get('profile_views', 0)}</li>
                    <li><strong>New Project Matches:</strong> {ctx.get('new_matches', 0)}</li>
                </ul>
                <h3>Trending Projects:</h3>
                <ul>{projects_list}</ul>
                <p><a href="{ctx.get('digest_url', '#')}" class="btn">View Full Digest</a></p>
            """
            plain_content = f"Weekly Digest for {user_name}\n\nProfile Views: {ctx.get('profile_views', 0)}\nNew Matches: {ctx.get('new_matches', 0)}\nView full digest: {ctx.get('digest_url', '#')}"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }}
        .header {{ background-color: #0f172a; padding: 24px; text-align: center; border-bottom: 1px solid #334155; }}
        .header h1 {{ color: #05b7d7; margin: 0; font-size: 24px; font-weight: 800; }}
        .content {{ padding: 32px 24px; line-height: 1.6; color: #cbd5e1; }}
        .content h2 {{ color: #ffffff; margin-top: 0; }}
        .btn {{ display: inline-block; background-color: #05b7d7; color: #ffffff !important; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 16px; }}
        .footer {{ background-color: #0f172a; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #334155; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>DevLink</h1>
        </div>
        <div class="content">
            {body_content}
        </div>
        <div class="footer">
            &copy; 2026 DevLink Collaboration Platform. All rights reserved.
        </div>
    </div>
</body>
</html>"""

        return EmailRenderResponse(
            template_type=template_type,
            subject=subject,
            html_content=html_content,
            text_content=plain_content,
        )
