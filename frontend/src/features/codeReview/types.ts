/**
 * Code Review & Mentorship Matching System
 * Type definitions for reviews, mentorship, feedback, and learning progress
 */

export type ReviewStatus = 'pending' | 'in-progress' | 'completed' | 'needs-changes' | 'approved';
export type ReviewType = 'pr-review' | 'code-audit' | 'architecture' | 'performance' | 'security' | 'learning';
export type FeedbackSeverity = 'critical' | 'major' | 'minor' | 'suggestion' | 'praise';
export type MentorMatchScore = 'perfect' | 'strong' | 'good' | 'fair';
export type MentorshipStatus = 'requesting' | 'active' | 'paused' | 'completed' | 'expired';
export type MentorshipFocus = 'career' | 'technical' | 'leadership' | 'interview-prep' | 'open-source';
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export interface CodeReview {
  id: string;
  title: string;
  description: string;
  type: ReviewType;
  status: ReviewStatus;
  repoUrl: string;
  prUrl: string | null;
  fileCount: number;
  linesChanged: number;
  author: string;
  authorAvatar: string;
  reviewer: string | null;
  reviewerAvatar: string | null;
  submittedAt: string;
  completedAt: string | null;
  feedbackCount: number;
  severityBreakdown: Record<FeedbackSeverity, number>;
  qualityScore: number; // 0-100
  tags: string[];
}

export interface FeedbackItem {
  id: string;
  reviewId: string;
  severity: FeedbackSeverity;
  category: string;
  file: string;
  line: number;
  message: string;
  suggestion: string | null;
  author: string;
  createdAt: string;
  resolved: boolean;
}

export interface MentorProfile {
  id: string;
  name: string;
  username: string;
  avatar: string;
  title: string;
  company: string;
  expertise: string[];
  yearsExperience: number;
  mentorshipStyle: string;
  maxMentees: number;
  currentMentees: number;
  rating: number;
  reviewCount: number;
  responseTime: string;
  available: boolean;
  bio: string;
}

export interface MentorMatch {
  mentorId: string;
  mentor: MentorProfile;
  matchScore: MentorMatchScore;
  matchPercentage: number;
  matchReasons: string[];
  skillOverlap: string[];
  focusAreas: MentorshipFocus[];
}

export interface MentorshipSession {
  id: string;
  mentorId: string;
  mentorName: string;
  menteeId: string;
  menteeName: string;
  status: MentorshipStatus;
  focus: MentorshipFocus;
  startDate: string;
  endDate: string | null;
  sessionsCompleted: number;
  totalSessions: number;
  nextSession: string | null;
  goals: string[];
  notes: string;
  rating: number | null;
}

export interface ReviewActivity {
  id: string;
  type: 'review-submitted' | 'feedback-added' | 'review-completed' | 'mentorship-request' | 'session-scheduled';
  message: string;
  timestamp: string;
  actor: string;
}

export interface CodeReviewInsight {
  id: string;
  type: 'tip' | 'warning' | 'success' | 'info';
  title: string;
  description: string;
  metric?: string;
  value?: string;
  actionable: boolean;
}

export interface CodeReviewSummary {
  totalReviews: number;
  completedReviews: number;
  avgQualityScore: number;
  totalFeedback: number;
  mentorshipSessions: number;
  activeMentorships: number;
  mentorRating: number;
  reviewStreak: number;
}

// ============================================================================
// Helper Utilities
// ============================================================================

export const REVIEW_STATUS_COLORS: Record<ReviewStatus, string> = {
  pending: '#9e9e9e',
  'in-progress': '#2196f3',
  completed: '#4caf50',
  'needs-changes': '#ff9800',
  approved: '#ffd700',
};

export const REVIEW_TYPE_ICONS: Record<ReviewType, string> = {
  'pr-review': '🔀',
  'code-audit': '🔍',
  architecture: '🏗️',
  performance: '⚡',
  security: '🔒',
  learning: '📚',
};

export const SEVERITY_COLORS: Record<FeedbackSeverity, string> = {
  critical: '#f44336',
  major: '#ff9800',
  minor: '#ffeb3b',
  suggestion: '#2196f3',
  praise: '#4caf50',
};

export const SEVERITY_ICONS: Record<FeedbackSeverity, string> = {
  critical: '🔴',
  major: '🟠',
  minor: '🟡',
  suggestion: '🔵',
  praise: '🟢',
};

export const MATCH_SCORE_COLORS: Record<MentorMatchScore, string> = {
  perfect: '#ffd700',
  strong: '#4caf50',
  good: '#2196f3',
  fair: '#9e9e9e',
};

export const FOCUS_ICONS: Record<MentorshipFocus, string> = {
  career: '🎯',
  technical: '⚙️',
  leadership: '👑',
  'interview-prep': '🎤',
  'open-source': '📦',
};

export const STATUS_COLORS: Record<MentorshipStatus, string> = {
  requesting: '#ff9800',
  active: '#4caf50',
  paused: '#9e9e9e',
  completed: '#2196f3',
  expired: '#f44336',
};

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
