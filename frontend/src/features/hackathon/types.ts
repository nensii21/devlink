/**
 * Hackathon Dashboard — Team formation, project submission, and judging
 * Type definitions for hackathons, teams, submissions, judges, and awards
 */

export type HackathonStatus = 'upcoming' | 'registration' | 'in-progress' | 'judging' | 'completed' | 'cancelled';
export type TeamRole = 'captain' | 'member' | 'mentor';
export type SubmissionStatus = 'draft' | 'submitted' | 'under-review' | 'finalist' | 'winner';
export type JudgeScoreCategory = 'innovation' | 'technical' | 'design' | 'impact' | 'presentation';
export type AwardTier = 'grand-prize' | 'runner-up' | 'third-place' | 'category' | 'honorable-mention' | 'special';
export type TeamSizeRange = 'solo' | 'duo' | 'small' | 'medium' | 'large';

export interface Hackathon {
  id: string;
  title: string;
  description: string;
  longDescription: string;
  status: HackathonStatus;
  theme: string;
  startDate: string;
  endDate: string;
  registrationDeadline: string;
  location: string;
  isVirtual: boolean;
  maxParticipants: number;
  currentParticipants: number;
  teamSizeRange: TeamSizeRange;
  prizes: { tier: string; amount: number; description: string }[];
  sponsors: string[];
  tracks: string[];
  rules: string[];
  tags: string[];
  organizerName: string;
  createdAt: string;
}

export interface Team {
  id: string;
  name: string;
  hackathonId: string;
  hackathonTitle: string;
  description: string;
  neededSkills: string[];
  members: TeamMember[];
  maxMembers: number;
  isOpen: boolean;
  hasSubmission: boolean;
  createdAt: string;
}

export interface TeamMember {
  id: string;
  name: string;
  username: string;
  avatar: string;
  role: TeamRole;
  skills: string[];
  joinedAt: string;
}

export interface Submission {
  id: string;
  title: string;
  description: string;
  teamId: string;
  teamName: string;
  hackathonId: string;
  hackathonTitle: string;
  status: SubmissionStatus;
  techStack: string[];
  repoUrl: string;
  demoUrl: string | null;
  videoUrl: string | null;
  track: string;
  submittedAt: string;
  scores: JudgeScore[];
  totalScore: number;
  rank: number | null;
  award: AwardTier | null;
  screenshots: string[];
}

export interface JudgeScore {
  category: JudgeScoreCategory;
  score: number; // 1-10
  maxScore: number;
  comment: string;
}

export interface Judge {
  id: string;
  name: string;
  title: string;
  company: string;
  avatar: string;
  expertise: string[];
  scoreCount: number;
  avgScore: number;
}

export interface Award {
  id: string;
  tier: AwardTier;
  title: string;
  description: string;
  prize: number;
  teamId: string;
  teamName: string;
  submissionTitle: string;
  hackathonId: string;
  hackathonTitle: string;
  awardedAt: string;
}

export interface HackathonActivity {
  id: string;
  type: 'registration' | 'team-formation' | 'submission' | 'judging' | 'announcement';
  message: string;
  timestamp: string;
  actor: string;
}

export interface HackathonInsight {
  id: string;
  type: 'tip' | 'warning' | 'success' | 'info';
  title: string;
  description: string;
  metric?: string;
  value?: string;
  actionable: boolean;
}

export interface HackathonSummary {
  totalHackathons: number;
  activeHackathons: number;
  teamsFormed: number;
  submissions: number;
  awards: number;
  totalPrizes: number;
  avgTeamSize: number;
  participationRate: number;
}

// ============================================================================
// Helper Utilities
// ============================================================================

export const HACKATHON_STATUS_COLORS: Record<HackathonStatus, string> = {
  upcoming: '#2196f3',
  registration: '#ff9800',
  'in-progress': '#f44336',
  judging: '#9c27b0',
  completed: '#4caf50',
  cancelled: '#9e9e9e',
};

export const SUBMISSION_STATUS_COLORS: Record<SubmissionStatus, string> = {
  draft: '#9e9e9e',
  submitted: '#2196f3',
  'under-review': '#ff9800',
  finalist: '#9c27b0',
  winner: '#ffd700',
};

export const AWARD_TIER_COLORS: Record<AwardTier, string> = {
  'grand-prize': '#ffd700',
  'runner-up': '#c0c0c0',
  'third-place': '#cd7f32',
  category: '#9c27b0',
  'honorable-mention': '#2196f3',
  special: '#4caf50',
};

export const AWARD_TIER_ICONS: Record<AwardTier, string> = {
  'grand-prize': '🏆',
  'runner-up': '🥈',
  'third-place': '🥉',
  category: '🎯',
  'honorable-mention': '⭐',
  special: '✨',
};

export const SCORE_CATEGORIES: { key: JudgeScoreCategory; label: string; icon: string }[] = [
  { key: 'innovation', label: 'Innovation', icon: '💡' },
  { key: 'technical', label: 'Technical', icon: '⚙️' },
  { key: 'design', label: 'Design', icon: '🎨' },
  { key: 'impact', label: 'Impact', icon: '🌍' },
  { key: 'presentation', label: 'Presentation', icon: '🎤' },
];

export function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

export function formatRelativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return 'Just now';
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return `${Math.floor(days / 30)}mo ago`;
}
