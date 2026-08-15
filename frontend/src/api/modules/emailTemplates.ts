import { api } from '../client';

export type EmailTemplateType =
  | 'welcome'
  | 'password_reset'
  | 'email_verification'
  | 'team_invitation'
  | 'project_accepted'
  | 'project_rejected'
  | 'weekly_digest';

export interface EmailTemplateInfo {
  template_type: EmailTemplateType;
  name: string;
  description: string;
  sample_context: Record<string, any>;
}

export interface EmailRenderResponse {
  template_type: EmailTemplateType;
  subject: string;
  html_content: string;
  text_content: string;
}

const DEFAULT_TEMPLATES: EmailTemplateInfo[] = [
  {
    template_type: 'welcome',
    name: 'Welcome Email',
    description: 'Sent to newly registered developers welcoming them to DevLink.',
    sample_context: { user_name: 'Alex Mercer', action_url: 'https://devlink.app/dashboard' },
  },
  {
    template_type: 'password_reset',
    name: 'Password Reset',
    description: 'Transactional email containing password reset link and security instructions.',
    sample_context: { user_name: 'Alex Mercer', reset_url: 'https://devlink.app/reset-password?token=sample123', expires_in_minutes: 30 },
  },
  {
    template_type: 'email_verification',
    name: 'Email Verification',
    description: 'Sent to verify developer email address upon sign up or email change.',
    sample_context: { user_name: 'Alex Mercer', verify_url: 'https://devlink.app/verify-email?code=987654' },
  },
  {
    template_type: 'team_invitation',
    name: 'Team Invitation',
    description: 'Invites a user to join a project team or organization.',
    sample_context: { user_name: 'Alex Mercer', inviter_name: 'Sarah Connor', project_name: 'AI Code Assistant', invite_url: 'https://devlink.app/invites/abc12345' },
  },
  {
    template_type: 'project_accepted',
    name: 'Project Accepted',
    description: 'Notifies applicant that their application to a project team was accepted.',
    sample_context: { user_name: 'Alex Mercer', project_name: 'DevLink Open Source Engine', role_title: 'Fullstack Developer', workspace_url: 'https://devlink.app/projects/1' },
  },
  {
    template_type: 'project_rejected',
    name: 'Project Application Status Update',
    description: 'Polite notification for applications that were not selected.',
    sample_context: { user_name: 'Alex Mercer', project_name: 'DevLink Open Source Engine', feedback_url: 'https://devlink.app/projects' },
  },
  {
    template_type: 'weekly_digest',
    name: 'Weekly Developer Digest',
    description: 'Summary of developer recommendations, profile views, and team activity.',
    sample_context: { user_name: 'Alex Mercer', profile_views: 42, new_matches: 5, trending_projects: ['AI Code Reviewer', 'Cloud Native Dashboard'], digest_url: 'https://devlink.app/digest' },
  },
];

export const listEmailTemplates = async (): Promise<EmailTemplateInfo[]> => {
  try {
    return await api.get<EmailTemplateInfo[]>('/email-templates');
  } catch {
    return DEFAULT_TEMPLATES;
  }
};

export const renderEmailTemplate = async (
  templateType: EmailTemplateType,
  context: Record<string, any> = {}
): Promise<EmailRenderResponse> => {
  try {
    return await api.post<EmailRenderResponse>('/email-templates/render', {
      template_type: templateType,
      context,
    });
  } catch {
    const tpl = DEFAULT_TEMPLATES.find((t) => t.template_type === templateType) || DEFAULT_TEMPLATES[0];
    const user_name = context.user_name || 'Alex Mercer';
    return {
      template_type: templateType,
      subject: `${tpl.name} for ${user_name}`,
      html_content: `<!DOCTYPE html><html><body style="background-color:#0f172a;color:#f8fafc;font-family:sans-serif;padding:24px;"><div style="max-width:600px;margin:0 auto;background-color:#1e293b;border-radius:12px;padding:32px;border:1px solid #334155;"><h1 style="color:#6366f1;">DevLink</h1><h2>${tpl.name}</h2><p>Hello ${user_name}, ${tpl.description}</p><a href="#" style="display:inline-block;background-color:#6366f1;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:16px;">Take Action</a></div></body></html>`,
      text_content: `${tpl.name}\n\nHello ${user_name},\n${tpl.description}\n\nVisit DevLink: https://devlink.app`,
    };
  }
};
