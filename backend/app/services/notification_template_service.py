from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class TemplateRenderError(Exception):
    pass


@dataclass
class NotificationTemplate:
    event_type: str
    title_template: str
    message_template: str
    channels: list[str] | None = None

    def render_title(self, variables: dict[str, Any]) -> str:
        return _interpolate(self.title_template, variables)

    def render_message(self, variables: dict[str, Any]) -> str:
        return _interpolate(self.message_template, variables)


DEFAULT_TEMPLATES: dict[str, NotificationTemplate] = {
    "project_invite": NotificationTemplate(
        event_type="project_invite",
        title_template="You've been invited to {{project_name}}",
        message_template=(
            "{{inviter_name}} has invited you to join the project"
            " '{{project_name}}'. <a href='{{project_url}}'>View invitation</a>."
        ),
        channels=["in_app", "email"],
    ),
    "application_accepted": NotificationTemplate(
        event_type="application_accepted",
        title_template="Application accepted for {{project_name}}",
        message_template=(
            "Your application to join '{{project_name}}' has been accepted by"
            " {{accepted_by}}. <a href='{{project_url}}'>View project</a>."
        ),
        channels=["in_app", "email"],
    ),
    "new_follower": NotificationTemplate(
        event_type="new_follower",
        title_template="{{follower_name}} started following you",
        message_template=(
            "<a href='{{follower_url}}'>{{follower_name}}</a> started following you."
        ),
        channels=["in_app"],
    ),
    "password_reset": NotificationTemplate(
        event_type="password_reset",
        title_template="Password reset successful",
        message_template=(
            "Your DevLink password has been reset successfully."
            " If you did not request this change, please contact support immediately."
            " <a href='{{support_url}}'>Contact support</a>."
        ),
        channels=["email"],
    ),
    "mention": NotificationTemplate(
        event_type="mention",
        title_template="{{mentioner_name}} mentioned you in {{context}}",
        message_template=(
            "<a href='{{mentioner_url}}'>{{mentioner_name}}</a> mentioned you in"
            " {{context}}. <a href='{{context_url}}'>View</a>."
        ),
        channels=["in_app", "email"],
    ),
    "system_announcement": NotificationTemplate(
        event_type="system_announcement",
        title_template="{{title}}",
        message_template="{{message}}",
        channels=["in_app", "email"],
    ),
}


def _interpolate(template: str, variables: dict[str, Any]) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in variables:
            raise TemplateRenderError(
                f"Missing variable '{key}' in template. Available: {list(variables.keys())}"
            )
        return str(variables[key])

    return re.sub(r"\{\{(\w+)\}\}", replace, template)


class NotificationTemplateService:
    def __init__(self, custom_templates: dict[str, NotificationTemplate] | None = None):
        self._templates: dict[str, NotificationTemplate] = {}
        self._templates.update(DEFAULT_TEMPLATES)
        if custom_templates:
            self._templates.update(custom_templates)

    def get_template(self, event_type: str) -> NotificationTemplate | None:
        return self._templates.get(event_type)

    def render(
        self, event_type: str, variables: dict[str, Any]
    ) -> tuple[str, str] | None:
        tmpl = self.get_template(event_type)
        if not tmpl:
            return None
        return tmpl.render_title(variables), tmpl.render_message(variables)

    def supports_channel(self, event_type: str, channel: str) -> bool:
        tmpl = self.get_template(event_type)
        if not tmpl or not tmpl.channels:
            return False
        return channel in tmpl.channels

    def list_event_types(self) -> list[str]:
        return list(self._templates.keys())

    def register_template(self, template: NotificationTemplate) -> None:
        self._templates[template.event_type] = template
