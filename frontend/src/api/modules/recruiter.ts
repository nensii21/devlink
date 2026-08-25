import { api } from "../client";
import type { ApplicationStatus } from "@/lib/api";

export interface ApplicationResponse {
  id: string;
  applicant_id: string;
  project_id: string;
  flare_id: string;
  status: ApplicationStatus;
  message?: string;
  portfolio_url?: string;
  github_url?: string;
  resume_url?: string;
  review_notes?: string;
  shortlisted: boolean;
  interview_scheduled_at?: string;
  interview_link?: string;
  created_at: string;
  updated_at: string;
}

export const recruiterApi = {
  getProjectApplications: (projectId: string) =>
    api.get<ApplicationResponse[]>(`/api/applications/project/${projectId}`),

  shortlistApplication: (applicationId: string, shortlisted: boolean) =>
    api.patch<ApplicationResponse>(`/api/applications/${applicationId}/shortlist`, {
      shortlisted,
    }),

  scheduleInterview: (
    applicationId: string,
    data: { interview_scheduled_at: string; interview_link?: string },
  ) =>
    api.patch<ApplicationResponse>(`/api/applications/${applicationId}/schedule_interview`, data),

  addNotes: (applicationId: string, notes: string | null) =>
    api.patch<ApplicationResponse>(`/api/applications/${applicationId}/notes`, { notes }),
};
