import type {
  CodeReview, FeedbackItem, MentorProfile, MentorMatch,
  MentorshipSession, ReviewActivity, CodeReviewInsight, CodeReviewSummary,
} from './types';

// ============================================================================
// Code Reviews
// ============================================================================

export const mockReviews: CodeReview[] = [
  {
    id: 'cr-001', title: 'React Hook Optimization PR', description: 'Refactor custom hooks to use memoization and reduce unnecessary re-renders',
    type: 'performance', status: 'completed', repoUrl: 'https://github.com/example/app', prUrl: 'https://github.com/example/app/pull/42',
    fileCount: 8, linesChanged: 245, author: 'Sarah Chen', authorAvatar: '',
    reviewer: 'Mike Rodriguez', reviewerAvatar: '', submittedAt: '2026-08-22T10:00:00Z',
    completedAt: '2026-08-23T14:00:00Z', feedbackCount: 12,
    severityBreakdown: { critical: 0, major: 2, minor: 4, suggestion: 3, praise: 3 },
    qualityScore: 82, tags: ['react', 'performance', 'hooks'],
  },
  {
    id: 'cr-002', title: 'FastAPI Authentication Module', description: 'New JWT authentication with refresh tokens and role-based access control',
    type: 'security', status: 'in-progress', repoUrl: 'https://github.com/example/api', prUrl: 'https://github.com/example/api/pull/18',
    fileCount: 12, linesChanged: 520, author: 'Alex Kim', authorAvatar: '',
    reviewer: null, reviewerAvatar: null, submittedAt: '2026-08-24T08:00:00Z',
    completedAt: null, feedbackCount: 0,
    severityBreakdown: { critical: 0, major: 0, minor: 0, suggestion: 0, praise: 0 },
    qualityScore: 0, tags: ['python', 'fastapi', 'auth', 'security'],
  },
  {
    id: 'cr-003', title: 'TypeScript Strict Mode Migration', description: 'Migrate codebase to strict TypeScript with proper type guards and assertions',
    type: 'code-audit', status: 'approved', repoUrl: 'https://github.com/example/frontend', prUrl: 'https://github.com/example/frontend/pull/89',
    fileCount: 34, linesChanged: 1280, author: 'Emma Wilson', authorAvatar: '',
    reviewer: 'Jordan Patel', reviewerAvatar: '', submittedAt: '2026-08-18T09:00:00Z',
    completedAt: '2026-08-20T16:00:00Z', feedbackCount: 28,
    severityBreakdown: { critical: 1, major: 5, minor: 12, suggestion: 6, praise: 4 },
    qualityScore: 75, tags: ['typescript', 'strict-mode', 'migration'],
  },
  {
    id: 'cr-004', title: 'Kubernetes Deployment Config', description: 'Helm charts and K8s manifests for production deployment with health checks',
    type: 'architecture', status: 'needs-changes', repoUrl: 'https://github.com/example/infra', prUrl: 'https://github.com/example/infra/pull/15',
    fileCount: 6, linesChanged: 180, author: 'Jordan Patel', authorAvatar: '',
    reviewer: 'Emma Wilson', reviewerAvatar: '', submittedAt: '2026-08-23T11:00:00Z',
    completedAt: null, feedbackCount: 8,
    severityBreakdown: { critical: 1, major: 2, minor: 3, suggestion: 2, praise: 0 },
    qualityScore: 55, tags: ['kubernetes', 'helm', 'devops'],
  },
  {
    id: 'cr-005', title: 'D3.js Data Visualization Library', description: 'Reusable chart components built on D3 with TypeScript generics',
    type: 'learning', status: 'completed', repoUrl: 'https://github.com/example/charts', prUrl: 'https://github.com/example/charts/pull/7',
    fileCount: 10, linesChanged: 420, author: 'Priya Sharma', authorAvatar: '',
    reviewer: 'Sarah Chen', reviewerAvatar: '', submittedAt: '2026-08-20T14:00:00Z',
    completedAt: '2026-08-21T10:00:00Z', feedbackCount: 15,
    severityBreakdown: { critical: 0, major: 1, minor: 6, suggestion: 5, praise: 3 },
    qualityScore: 88, tags: ['d3', 'typescript', 'data-viz', 'learning'],
  },
];

// ============================================================================
// Feedback Items
// ============================================================================

export const mockFeedback: FeedbackItem[] = [
  { id: 'fb-001', reviewId: 'cr-001', severity: 'major', category: 'Performance', file: 'hooks/useDebounce.ts', line: 24, message: 'Missing cleanup in useEffect — potential memory leak', suggestion: 'Add cleanup function to cancel pending timeout', author: 'Mike Rodriguez', createdAt: '2026-08-22T14:00:00Z', resolved: true },
  { id: 'fb-002', reviewId: 'cr-001', severity: 'praise', category: 'Code Quality', file: 'hooks/useInfiniteScroll.ts', line: 1, message: 'Excellent use of IntersectionObserver — clean and performant', suggestion: null, author: 'Mike Rodriguez', createdAt: '2026-08-22T14:30:00Z', resolved: true },
  { id: 'fb-003', reviewId: 'cr-001', severity: 'minor', category: 'TypeScript', file: 'hooks/useLocalStorage.ts', line: 15, message: 'Could use a generic type for better type safety', suggestion: 'Use <T> generic instead of `any` for the value parameter', author: 'Mike Rodriguez', createdAt: '2026-08-22T15:00:00Z', resolved: true },
  { id: 'fb-004', reviewId: 'cr-001', severity: 'suggestion', category: 'Testing', file: 'hooks/useDebounce.test.ts', line: 1, message: 'Add edge case tests for rapid state changes', suggestion: 'Test with 0ms delay and concurrent updates', author: 'Mike Rodriguez', createdAt: '2026-08-22T16:00:00Z', resolved: false },
  { id: 'fb-005', reviewId: 'cr-003', severity: 'critical', category: 'Type Safety', file: 'utils/validators.ts', line: 42, message: 'Unchecked null assertion — will crash at runtime', suggestion: 'Add null check before accessing .value property', author: 'Jordan Patel', createdAt: '2026-08-19T10:00:00Z', resolved: true },
  { id: 'fb-006', reviewId: 'cr-003', severity: 'major', category: 'TypeScript', file: 'types/api.ts', line: 18, message: 'Use discriminated unions instead of type assertion', suggestion: 'Replace `as` casts with proper union types', author: 'Jordan Patel', createdAt: '2026-08-19T11:00:00Z', resolved: true },
];

// ============================================================================
// Mentor Profiles
// ============================================================================

export const mockMentors: MentorProfile[] = [
  { id: 'ment-001', name: 'Sarah Chen', username: 'sarahchen', avatar: '', title: 'Senior Frontend Engineer', company: 'Stripe', expertise: ['React', 'TypeScript', 'Performance', 'Architecture'], yearsExperience: 8, mentorshipStyle: 'Hands-on code reviews with detailed explanations', maxMentees: 3, currentMentees: 1, rating: 4.9, reviewCount: 156, responseTime: '< 2 hours', available: true, bio: 'Passionate about clean code and developer experience.' },
  { id: 'ment-002', name: 'Alex Kim', username: 'alexkim', avatar: '', title: 'ML Engineer', company: 'OpenAI', expertise: ['Python', 'ML', 'TensorFlow', 'System Design'], yearsExperience: 6, mentorshipStyle: 'Project-based learning with real-world datasets', maxMentees: 2, currentMentees: 2, rating: 4.7, reviewCount: 89, responseTime: '< 4 hours', available: false, bio: 'Building intelligent systems and mentoring the next generation.' },
  { id: 'ment-003', name: 'Emma Wilson', username: 'emmawilson', avatar: '', title: 'DevOps Lead', company: 'Netflix', expertise: ['Kubernetes', 'AWS', 'CI/CD', 'Infrastructure'], yearsExperience: 10, mentorshipStyle: 'Structured curriculum with hands-on labs', maxMentees: 4, currentMentees: 2, rating: 4.8, reviewCount: 112, responseTime: '< 6 hours', available: true, bio: 'Cloud infrastructure expert. Love teaching DevOps practices.' },
  { id: 'ment-004', name: 'Marcus Johnson', username: 'marcusj', avatar: '', title: 'CTO', company: 'Stripe', expertise: ['Architecture', 'Leadership', 'Career Growth', 'Startups'], yearsExperience: 15, mentorshipStyle: 'Strategic career guidance and leadership coaching', maxMentees: 2, currentMentees: 1, rating: 5.0, reviewCount: 67, responseTime: '< 24 hours', available: true, bio: 'Former startup founder. Now helping others grow as engineering leaders.' },
];

// ============================================================================
// Mentor Matches
// ============================================================================

export const mockMatches: MentorMatch[] = [
  { mentorId: 'ment-001', mentor: mockMentors[0], matchScore: 'perfect', matchPercentage: 92, matchReasons: ['Same tech stack (React/TS)', 'Both focus on performance', 'Available'], skillOverlap: ['React', 'TypeScript', 'Performance'], focusAreas: ['technical', 'career'] },
  { mentorId: 'ment-003', mentor: mockMentors[2], matchScore: 'strong', matchPercentage: 78, matchReasons: ['DevOps expertise needed', 'Structured learning style fits'], skillOverlap: ['Kubernetes', 'CI/CD'], focusAreas: ['technical'] },
  { mentorId: 'ment-004', mentor: mockMentors[3], matchScore: 'good', matchPercentage: 65, matchReasons: ['Career growth interest', 'Leadership guidance'], skillOverlap: [], focusAreas: ['career', 'leadership'] },
];

// ============================================================================
// Mentorship Sessions
// ============================================================================

export const mockSessions: MentorshipSession[] = [
  {
    id: 'ms-001', mentorId: 'ment-001', mentorName: 'Sarah Chen', menteeId: 'user-001', menteeName: 'You',
    status: 'active', focus: 'technical', startDate: '2026-07-01T10:00:00Z', endDate: null,
    sessionsCompleted: 6, totalSessions: 12, nextSession: '2026-08-26T14:00:00Z',
    goals: ['Master React patterns', 'Improve code review skills', 'Build production app'], notes: 'Focusing on hooks and performance optimization.',
    rating: null,
  },
  {
    id: 'ms-002', mentorId: 'ment-003', mentorName: 'Emma Wilson', menteeId: 'user-001', menteeName: 'You',
    status: 'active', focus: 'technical', startDate: '2026-08-01T10:00:00Z', endDate: null,
    sessionsCompleted: 2, totalSessions: 8, nextSession: '2026-08-28T10:00:00Z',
    goals: ['Learn Kubernetes', 'Master CI/CD pipelines', 'Understand cloud architecture'], notes: 'Started with Docker basics, moving to K8s next week.',
    rating: null,
  },
  {
    id: 'ms-003', mentorId: 'ment-004', mentorName: 'Marcus Johnson', menteeId: 'user-001', menteeName: 'You',
    status: 'completed', focus: 'career', startDate: '2026-03-01T10:00:00Z', endDate: '2026-06-30T10:00:00Z',
    sessionsCompleted: 8, totalSessions: 8, nextSession: null,
    goals: ['Define career path', 'Build leadership skills', 'Prepare for senior role'], notes: 'Great mentorship experience. Laid out clear growth plan.',
    rating: 5,
  },
];

// ============================================================================
// Activities
// ============================================================================

export const mockActivities: ReviewActivity[] = [
  { id: 'rac-001', type: 'review-submitted', message: 'New review submitted: "FastAPI Authentication Module"', timestamp: '2026-08-24T08:00:00Z', actor: 'Alex Kim' },
  { id: 'rac-002', type: 'feedback-added', message: 'Sarah Chen added feedback to "React Hook Optimization PR"', timestamp: '2026-08-23T14:00:00Z', actor: 'Sarah Chen' },
  { id: 'rac-003', type: 'review-completed', message: '"React Hook Optimization PR" review completed — score: 82/100', timestamp: '2026-08-23T14:00:00Z', actor: 'Mike Rodriguez' },
  { id: 'rac-004', type: 'mentorship-request', message: 'Mentorship session scheduled with Emma Wilson (K8s basics)', timestamp: '2026-08-22T10:00:00Z', actor: 'You' },
  { id: 'rac-005', type: 'session-scheduled', message: 'Next mentorship session with Sarah Chen: Aug 26 at 2PM', timestamp: '2026-08-21T09:00:00Z', actor: 'Sarah Chen' },
];

// ============================================================================
// Insights
// ============================================================================

export const mockInsights: CodeReviewInsight[] = [
  { id: 'cri-001', type: 'success', title: 'High Quality Reviews', description: 'Your completed reviews average 85/100 quality score — well above the 70 average.', metric: 'Quality Score', value: '85/100', actionable: false },
  { id: 'cri-002', type: 'tip', title: 'Review FastAPI PR', description: 'Alex Kim\'s "FastAPI Authentication Module" PR needs a security-focused reviewer. Your expertise matches.', metric: 'Match', value: 'Security', actionable: true },
  { id: 'cri-003', type: 'info', title: 'Mentorship Progress', description: 'You\'re 50% through your mentorship with Sarah Chen. 6 of 12 sessions completed.', metric: 'Progress', value: '50%', actionable: false },
  { id: 'cri-004', type: 'warning', title: 'Pending Review', description: 'Kubernetes Deployment Config PR has 2 critical issues that need attention.', metric: 'Critical Issues', value: '2', actionable: true },
];

// ============================================================================
// Summary
// ============================================================================

export const mockCodeReviewSummary: CodeReviewSummary = {
  totalReviews: 5,
  completedReviews: 3,
  avgQualityScore: 82,
  totalFeedback: 63,
  mentorshipSessions: 2,
  activeMentorships: 2,
  mentorRating: 4.9,
  reviewStreak: 12,
};
