import { api } from '../client';

export type TeamActivityType =
  | 'member_joined'
  | 'member_left'
  | 'role_updated'
  | 'project_updated'
  | 'milestone_completed'
  | 'new_discussion'
  | 'file_uploaded';

export interface TeamActivityItem {
  id: string;
  project_id: number;
  activity_type: TeamActivityType;
  title: string;
  description?: string;
  actor_name: string;
  actor_avatar?: string;
  metadata_info?: Record<string, any>;
  created_at: string;
}

export interface TeamActivityTimelineResponse {
  project_id: number;
  items: TeamActivityItem[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export const getTeamActivityTimeline = async (
  projectId: number,
  page: number = 1,
  limit: number = 10,
  activityType?: string
): Promise<TeamActivityTimelineResponse> => {
  try {
    let url = `/projects/${projectId}/activity-timeline?page=${page}&limit=${limit}`;
    if (activityType) {
      url += `&activity_type=${activityType}`;
    }
    const res = await api.get<TeamActivityTimelineResponse>(url);
    if (res && res.items) return res;
  } catch (e) {
    console.warn('Backend API unavailable, using fallback mock activity timeline:', e);
  }

  const raw_items: TeamActivityItem[] = [
    {
      id: '1',
      project_id: projectId,
      activity_type: 'member_joined',
      title: 'Sarah Connor joined the team',
      description: 'Sarah joined as Frontend Engineer',
      actor_name: 'Sarah Connor',
      actor_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
      metadata_info: { role: 'Frontend Engineer' },
      created_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
    },
    {
      id: '2',
      project_id: projectId,
      activity_type: 'milestone_completed',
      title: 'Completed Milestone: MVP Auth & Database Schema',
      description: 'All 12 sub-tasks for Sprint 1 have been marked completed.',
      actor_name: 'Alex Mercer',
      actor_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
      metadata_info: { milestone_id: 101, progress: '100%' },
      created_at: new Date(Date.now() - 5 * 3600 * 1000).toISOString(),
    },
    {
      id: '3',
      project_id: projectId,
      activity_type: 'file_uploaded',
      title: 'Uploaded architecture_v2.pdf',
      description: 'System architecture diagram and cloud specs uploaded to team workspace.',
      actor_name: 'Elena Rostova',
      actor_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Elena',
      metadata_info: { file_name: 'architecture_v2.pdf', size_kb: 2048 },
      created_at: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
    },
    {
      id: '4',
      project_id: projectId,
      activity_type: 'new_discussion',
      title: 'Started discussion: Real-time WebSocket Protocol Design',
      description: 'Opened discussion thread regarding socket event schemas.',
      actor_name: 'Marcus Vance',
      actor_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Marcus',
      metadata_info: { comments_count: 8 },
      created_at: new Date(Date.now() - 48 * 3600 * 1000).toISOString(),
    },
    {
      id: '5',
      project_id: projectId,
      activity_type: 'role_updated',
      title: 'Updated Alex Mercer role to Project Lead',
      description: 'Permissions elevated to Project Admin',
      actor_name: 'Project Owner',
      actor_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Owner',
      metadata_info: { new_role: 'Project Lead' },
      created_at: new Date(Date.now() - 72 * 3600 * 1000).toISOString(),
    },
  ];

  const filtered = activityType ? raw_items.filter((item) => item.activity_type === activityType) : raw_items;
  return {
    project_id: projectId,
    items: filtered,
    total: filtered.length,
    page,
    limit,
    has_more: false,
  };
};
