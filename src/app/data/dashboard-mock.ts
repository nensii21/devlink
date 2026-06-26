export interface StatItem {
  id: string;
  title: string;
  value: string;
  trend: number;
  trendLabel: string;
  icon: 'Briefcase' | 'Users' | 'MailOpen' | 'Sparkles';
}

export interface ActivityItem {
  id: string;
  type: 'joining' | 'update' | 'invite' | 'connection' | 'flare_expire' | 'message';
  title: string;
  description: string;
  time: string;
  status: 'info' | 'success' | 'warning' | 'error';
}

export interface Builder {
  id: string;
  name: string;
  role: string;
  skills: string[];
  location: string;
  experience: string;
  match: number;
  avatar: string;
  isVerified?: boolean;
}

export interface FlareRequest {
  id: string;
  builder: Builder;
  type: 'joining' | 'invite';
  expiresIn: string;
  availability: string;
}

export const MOCK_STATS: StatItem[] = [
  { id: '1', title: 'Active Projects', value: '12', trend: 8, trendLabel: 'vs last week', icon: 'Briefcase' },
  { id: '2', title: 'Team Members', value: '48', trend: 12, trendLabel: 'vs last week', icon: 'Users' },
  { id: '3', title: 'Open Invites', value: '6', trend: -2, trendLabel: 'vs last week', icon: 'MailOpen' },
  { id: '4', title: 'AI Matches', value: '124', trend: 24, trendLabel: 'vs last week', icon: 'Sparkles' },
];

export const MOCK_ACTIVITIES: ActivityItem[] = [
  { id: '1', type: 'joining', title: 'New Builder Joined', description: 'Sarah Chen joined the "Nebula AI" project as a Senior Architect.', time: '2 hours ago', status: 'success' },
  { id: '2', type: 'flare_expire', title: "Builder's Flare Expired", description: 'Your request for "Frontend Engineer" has expired.', time: '5 hours ago', status: 'warning' },
  { id: '3', type: 'invite', title: 'Invitation Accepted', description: 'Alex Rivera accepted your invite to join the platform.', time: 'Yesterday', status: 'success' },
  { id: '4', type: 'update', title: 'Project Updated', description: 'Project "DevLink Core" was updated with 4 new tasks.', time: 'Yesterday', status: 'info' },
  { id: '5', type: 'message', title: 'New Message Received', description: 'You have a new message from Marcus Aurelius.', time: '2 days ago', status: 'info' },
];

export const MOCK_BUILDERS: Builder[] = [
  { id: '1', name: 'Elena Rodriguez', role: 'Full Stack Engineer', skills: ['React', 'Node.js', 'PostgreSQL'], location: 'Austin, TX', experience: '6 years', match: 98, avatar: 'https://i.pravatar.cc/150?u=elena', isVerified: true },
  { id: '2', name: 'Chen Wei', role: 'AI Researcher', skills: ['PyTorch', 'NLP', 'Python'], location: 'San Francisco, CA', experience: '4 years', match: 94, avatar: 'https://i.pravatar.cc/150?u=chen', isVerified: true },
  { id: '3', name: 'Jordan Smith', role: 'Product Designer', skills: ['Figma', 'UX Research', 'Design Systems'], location: 'Remote', experience: '8 years', match: 91, avatar: 'https://i.pravatar.cc/150?u=jordan' },
  { id: '4', name: 'Aisha Khan', role: 'DevOps Lead', skills: ['AWS', 'Kubernetes', 'Terraform'], location: 'London, UK', experience: '10 years', match: 88, avatar: 'https://i.pravatar.cc/150?u=aisha', isVerified: true },
];

export const MOCK_FLARE_REQUESTS: FlareRequest[] = [
  { 
    id: '1', 
    type: 'joining', 
    expiresIn: '13 Days', 
    availability: 'Full-time',
    builder: { id: 'b1', name: 'Marcus Aurelius', role: 'Smart Contract Developer', skills: ['Solidity', 'Rust'], location: 'Rome', experience: '5y', match: 96, avatar: 'https://i.pravatar.cc/150?u=marcus' } 
  },
  { 
    id: '2', 
    type: 'invite', 
    expiresIn: '8 Days', 
    availability: 'Part-time',
    builder: { id: 'b2', name: 'Hypatia', role: 'Data Scientist', skills: ['Python', 'R', 'Stats'], location: 'Alexandria', experience: '3y', match: 89, avatar: 'https://i.pravatar.cc/150?u=hypatia' } 
  },
];
