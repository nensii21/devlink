import type {
  Hackathon, Team, Submission, Judge, Award,
  HackathonActivity, HackathonInsight, HackathonSummary,
} from './types';

// ============================================================================
// Hackathons
// ============================================================================

export const mockHackathons: Hackathon[] = [
  {
    id: 'hx-001', title: 'DevLink Build Sprint 2026', description: '48-hour sprint to build innovative developer tools and productivity apps',
    longDescription: 'The flagship DevLink hackathon focused on building tools that make developers more productive. Open to all skill levels.',
    status: 'in-progress', theme: 'Developer Productivity',
    startDate: '2026-08-23T10:00:00Z', endDate: '2026-08-25T10:00:00Z',
    registrationDeadline: '2026-08-22T23:59:00Z',
    location: 'Online + SF Hub', isVirtual: true, maxParticipants: 500, currentParticipants: 342,
    teamSizeRange: 'small',
    prizes: [{ tier: 'grand-prize', amount: 5000, description: 'Best Overall Project' }, { tier: 'runner-up', amount: 2500, description: 'Second Best' }, { tier: 'third-place', amount: 1000, description: 'Third Best' }],
    sponsors: ['Vercel', 'Supabase', 'Railway', 'Clerk'],
    tracks: ['AI-Powered Tools', 'Developer Experience', 'Open Source', 'Social Impact'],
    rules: ['Teams of 2-4', 'New projects only', 'Open source required', 'Must have demo'],
    tags: ['developer-tools', 'productivity', '48h', 'flagship'],
    organizerName: 'DevLink Team', createdAt: '2026-07-01T10:00:00Z',
  },
  {
    id: 'hx-002', title: 'AI/ML Weekend Challenge', description: 'Build AI-powered applications in a weekend — focus on LLMs and generative AI',
    longDescription: 'A weekend hackathon focused on building practical AI applications using the latest LLMs, APIs, and frameworks.',
    status: 'upcoming', theme: 'AI & Generative AI',
    startDate: '2026-09-08T10:00:00Z', endDate: '2026-09-09T22:00:00Z',
    registrationDeadline: '2026-09-07T23:59:00Z',
    location: 'Online', isVirtual: true, maxParticipants: 300, currentParticipants: 156,
    teamSizeRange: 'small',
    prizes: [{ tier: 'grand-prize', amount: 3000, description: 'Best AI Application' }, { tier: 'category', amount: 1000, description: 'Best Use of LLMs' }],
    sponsors: ['OpenAI', 'Anthropic', 'Hugging Face'],
    tracks: ['LLM Applications', 'AI Agents', 'Data & Analytics', 'Creative AI'],
    rules: ['Teams of 1-3', 'Must use AI/ML', 'Demo required'],
    tags: ['ai', 'ml', 'llm', 'weekend'],
    organizerName: 'AI Community', createdAt: '2026-08-01T10:00:00Z',
  },
  {
    id: 'hx-003', title: 'Climate Tech Hackathon', description: 'Build technology solutions for climate change and environmental sustainability',
    longDescription: 'A hackathon focused on using technology to address climate change, environmental monitoring, and sustainability.',
    status: 'completed', theme: 'Climate & Sustainability',
    startDate: '2026-07-15T10:00:00Z', endDate: '2026-07-17T10:00:00Z',
    registrationDeadline: '2026-07-14T23:59:00Z',
    location: 'San Francisco, CA', isVirtual: false, maxParticipants: 200, currentParticipants: 178,
    teamSizeRange: 'medium',
    prizes: [{ tier: 'grand-prize', amount: 10000, description: 'Best Climate Solution' }, { tier: 'runner-up', amount: 5000, description: 'Runner Up' }],
    sponsors: ['Tesla', 'Google Climate', 'Patagonia'],
    tracks: ['Carbon Tracking', 'Renewable Energy', 'Environmental Monitoring', 'Sustainable Agriculture'],
    rules: ['Teams of 3-5', 'Real-world impact required', 'Open source'],
    tags: ['climate', 'sustainability', 'green-tech'],
    organizerName: 'Climate Tech Alliance', createdAt: '2026-06-01T10:00:00Z',
  },
];

// ============================================================================
// Teams
// ============================================================================

export const mockTeams: Team[] = [
  {
    id: 'team-001', name: 'CodeCrafters', hackathonId: 'hx-001', hackathonTitle: 'DevLink Build Sprint 2026',
    description: 'Building an AI-powered code review assistant that learns from your coding style',
    neededSkills: ['Python', 'LLMs', 'React'], maxMembers: 4, isOpen: false, hasSubmission: false,
    members: [
      { id: 'tm-001', name: 'Sarah Chen', username: 'sarahchen', avatar: '', role: 'captain', skills: ['React', 'TypeScript'], joinedAt: '2026-08-20T10:00:00Z' },
      { id: 'tm-002', name: 'Mike Rodriguez', username: 'mikerod', avatar: '', role: 'member', skills: ['Python', 'FastAPI'], joinedAt: '2026-08-20T11:00:00Z' },
      { id: 'tm-003', name: 'Alex Kim', username: 'alexkim', avatar: '', role: 'member', skills: ['ML', 'TensorFlow'], joinedAt: '2026-08-20T12:00:00Z' },
    ],
    createdAt: '2026-08-20T10:00:00Z',
  },
  {
    id: 'team-002', name: 'ShipFast', hackathonId: 'hx-001', hackathonTitle: 'DevLink Build Sprint 2026',
    description: 'A rapid prototyping tool that generates full-stack apps from natural language prompts',
    neededSkills: ['TypeScript', 'AI', 'UI/UX'], maxMembers: 3, isOpen: true, hasSubmission: true,
    members: [
      { id: 'tm-004', name: 'Emma Wilson', username: 'emmawilson', avatar: '', role: 'captain', skills: ['DevOps', 'AWS'], joinedAt: '2026-08-20T10:00:00Z' },
      { id: 'tm-005', name: 'Jordan Patel', username: 'jordanp', avatar: '', role: 'member', skills: ['Go', 'Rust'], joinedAt: '2026-08-20T14:00:00Z' },
    ],
    createdAt: '2026-08-20T10:00:00Z',
  },
  {
    id: 'team-003', name: 'GreenCode', hackathonId: 'hx-003', hackathonTitle: 'Climate Tech Hackathon',
    description: 'Carbon footprint tracker for developers — track your coding impact',
    neededSkills: ['React', 'Python', 'Data Viz'], maxMembers: 4, isOpen: false, hasSubmission: true,
    members: [
      { id: 'tm-006', name: 'Priya Sharma', username: 'priyasharma', avatar: '', role: 'captain', skills: ['React Native', 'TypeScript'], joinedAt: '2026-07-10T10:00:00Z' },
      { id: 'tm-007', name: 'Sarah Chen', username: 'sarahchen', avatar: '', role: 'member', skills: ['React', 'D3.js'], joinedAt: '2026-07-10T11:00:00Z' },
      { id: 'tm-008', name: 'Alex Kim', username: 'alexkim', avatar: '', role: 'mentor', skills: ['ML', 'Python'], joinedAt: '2026-07-10T12:00:00Z' },
    ],
    createdAt: '2026-07-10T10:00:00Z',
  },
];

// ============================================================================
// Submissions
// ============================================================================

export const mockSubmissions: Submission[] = [
  {
    id: 'sub-001', title: 'CodeLens AI', description: 'AI-powered code review assistant that learns from your coding patterns and provides personalized feedback',
    teamId: 'team-002', teamName: 'ShipFast', hackathonId: 'hx-003', hackathonTitle: 'Climate Tech Hackathon',
    status: 'winner', techStack: ['React', 'Python', 'OpenAI', 'FastAPI'], repoUrl: 'https://github.com/example/codelens',
    demoUrl: 'https://codelens.dev', videoUrl: null, track: 'AI-Powered Tools', submittedAt: '2026-07-17T08:00:00Z',
    scores: [
      { category: 'innovation', score: 9, maxScore: 10, comment: 'Novel approach to code review' },
      { category: 'technical', score: 8, maxScore: 10, comment: 'Solid implementation with LLM integration' },
      { category: 'design', score: 9, maxScore: 10, comment: 'Beautiful UI with great UX' },
      { category: 'impact', score: 8, maxScore: 10, comment: 'High impact for developer productivity' },
      { category: 'presentation', score: 9, maxScore: 10, comment: 'Excellent demo and explanation' },
    ],
    totalScore: 43, rank: 1, award: 'grand-prize', screenshots: [],
  },
  {
    id: 'sub-002', title: 'CarbonDev', description: 'Track and reduce your development carbon footprint with real-time analytics',
    teamId: 'team-003', teamName: 'GreenCode', hackathonId: 'hx-003', hackathonTitle: 'Climate Tech Hackathon',
    status: 'runner-up', techStack: ['React', 'Python', 'D3.js', 'PostgreSQL'], repoUrl: 'https://github.com/example/carbondev',
    demoUrl: null, videoUrl: null, track: 'Environmental Monitoring', submittedAt: '2026-07-17T09:00:00Z',
    scores: [
      { category: 'innovation', score: 8, maxScore: 10, comment: 'Creative use of data for environmental impact' },
      { category: 'technical', score: 7, maxScore: 10, comment: 'Good implementation, room for scalability' },
      { category: 'design', score: 8, maxScore: 10, comment: 'Clean, intuitive interface' },
      { category: 'impact', score: 9, maxScore: 10, comment: 'Direct environmental impact' },
      { category: 'presentation', score: 7, maxScore: 10, comment: 'Clear presentation' },
    ],
    totalScore: 39, rank: 2, award: 'runner-up', screenshots: [],
  },
];

// ============================================================================
// Judges
// ============================================================================

export const mockJudges: Judge[] = [
  { id: 'judge-001', name: 'Dr. Maya Patel', title: 'AI Research Lead', company: 'Google DeepMind', avatar: '', expertise: ['AI/ML', 'NLP', 'Computer Vision'], scoreCount: 24, avgScore: 7.8 },
  { id: 'judge-002', name: 'Chris Evans', title: 'VP of Engineering', company: 'Vercel', avatar: '', expertise: ['React', 'Next.js', 'Performance'], scoreCount: 31, avgScore: 8.2 },
  { id: 'judge-003', name: 'Lisa Zhang', title: 'Design Director', company: 'Figma', avatar: '', expertise: ['UI/UX', 'Design Systems', 'Accessibility'], scoreCount: 28, avgScore: 7.5 },
  { id: 'judge-004', name: 'Marcus Johnson', title: 'CTO', company: 'Stripe', avatar: '', expertise: ['Architecture', 'Payments', 'Scalability'], scoreCount: 19, avgScore: 8.5 },
];

// ============================================================================
// Awards
// ============================================================================

export const mockAwards: Award[] = [
  { id: 'aw-001', tier: 'grand-prize', title: 'Grand Prize Winner', description: 'Best overall project with highest scores across all categories', prize: 10000, teamId: 'team-003', teamName: 'GreenCode', submissionTitle: 'CarbonDev', hackathonId: 'hx-003', hackathonTitle: 'Climate Tech Hackathon', awardedAt: '2026-07-17T12:00:00Z' },
  { id: 'aw-002', tier: 'runner-up', title: 'Runner Up', description: 'Second best project', prize: 5000, teamId: 'team-002', teamName: 'ShipFast', submissionTitle: 'CodeLens AI', hackathonId: 'hx-003', hackathonTitle: 'Climate Tech Hackathon', awardedAt: '2026-07-17T12:00:00Z' },
  { id: 'aw-003', tier: 'category', title: 'Best AI Application', description: 'Most innovative use of AI/ML', prize: 1000, teamId: 'team-002', teamName: 'ShipFast', submissionTitle: 'CodeLens AI', hackathonId: 'hx-003', hackathonTitle: 'Climate Tech Hackathon', awardedAt: '2026-07-17T12:00:00Z' },
];

// ============================================================================
// Activities
// ============================================================================

export const mockActivities: HackathonActivity[] = [
  { id: 'act-001', type: 'registration', message: 'New team "ShipFast" registered for Build Sprint 2026', timestamp: '2026-08-24T09:30:00Z', actor: 'ShipFast' },
  { id: 'act-002', type: 'team-formation', message: 'Team "CodeCrafters" is looking for a ML engineer', timestamp: '2026-08-24T08:00:00Z', actor: 'Sarah Chen' },
  { id: 'act-003', type: 'submission', message: 'Team "ShipFast" submitted "AI Prototype Generator"', timestamp: '2026-08-24T07:00:00Z', actor: 'Emma Wilson' },
  { id: 'act-004', type: 'announcement', message: 'Judging for Climate Tech Hackathon has started', timestamp: '2026-07-17T10:00:00Z', actor: 'Admin' },
  { id: 'act-005', type: 'judging', message: 'Dr. Maya Patel scored 3 submissions', timestamp: '2026-07-17T11:00:00Z', actor: 'Dr. Maya Patel' },
];

// ============================================================================
// Insights
// ============================================================================

export const mockInsights: HackathonInsight[] = [
  { id: 'hi-001', type: 'success', title: 'Strong Participation', description: 'DevLink Build Sprint 2026 has 342 participants — 68% of capacity. Great engagement!', metric: 'Participation', value: '68%', actionable: false },
  { id: 'hi-002', type: 'tip', title: 'Join CodeCrafters', description: 'Team "CodeCrafters" needs an ML engineer. Your TensorFlow skills are a perfect match.', metric: 'Team Match', value: 'Perfect', actionable: true },
  { id: 'hi-003', type: 'info', title: 'AI/ML Challenge Soon', description: 'The AI/ML Weekend Challenge starts Sept 8. Register early — only 156 spots left.', metric: 'Spots Left', value: '144', actionable: true },
  { id: 'hi-004', type: 'warning', title: 'Submission Deadline Approaching', description: 'Build Sprint 2026 submission deadline is in 18 hours. 3 teams haven\'t submitted yet.', metric: 'Time Left', value: '18h', actionable: true },
];

// ============================================================================
// Summary
// ============================================================================

export const mockHackathonSummary: HackathonSummary = {
  totalHackathons: 3,
  activeHackathons: 1,
  teamsFormed: 12,
  submissions: 8,
  awards: 3,
  totalPrizes: 18500,
  avgTeamSize: 3.2,
  participationRate: 0.72,
};
