import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, AreaChart, Area,
  ComposedChart, Scatter, ScatterChart, ZAxis
} from 'recharts';

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#4f46e5', '#7c3aed', '#ede9fe', '#ddd6fe'];

export const ReviewQualityRadar = ({ data }: { data: { category: string; score: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <RadarChart data={data}>
      <PolarGrid stroke="#374151" />
      <PolarAngleAxis dataKey="category" tick={{ fill: '#9ca3af', fontSize: 12 }} />
      <PolarRadiusAxis tick={{ fill: '#6b7280', fontSize: 10 }} domain={[0, 10]} />
      <Radar name="Score" dataKey="score" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} strokeWidth={2} />
    </RadarChart>
  </ResponsiveContainer>
);

export const ReviewVolumeBar = ({ data }: { data: { day: string; reviews: number; comments: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <BarChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
      <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
      <Bar dataKey="reviews" fill="#6366f1" radius={[4, 4, 0, 0]} name="Reviews" />
      <Bar dataKey="comments" fill="#a78bfa" radius={[4, 4, 0, 0]} name="Comments" />
      <Legend wrapperStyle={{ color: '#9ca3af' }} />
    </BarChart>
  </ResponsiveContainer>
);

export const ResponseTimeBar = ({ data }: { data: { range: string; count: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <BarChart data={data} layout="vertical">
      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
      <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <YAxis type="category" dataKey="range" tick={{ fill: '#9ca3af', fontSize: 11 }} width={80} />
      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
      <Bar dataKey="count" fill="#4f46e5" radius={[0, 4, 4, 0]} />
    </BarChart>
  </ResponsiveContainer>
);

export const LanguagePie = ({ data }: { data: { language: string; reviews: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <PieChart>
      <Pie data={data} dataKey="reviews" nameKey="language" cx="50%" cy="50%" outerRadius={90} innerRadius={50} paddingAngle={3} label={({ language, percent }) => `${language} ${(percent * 100).toFixed(0)}%`} labelLine={{ stroke: '#6b7280' }}>
        {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
      </Pie>
      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
    </PieChart>
  </ResponsiveContainer>
);

export const MentorshipProgressLine = ({ data }: { data: { week: string; sessions: number; goals: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <LineChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
      <XAxis dataKey="week" tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
      <Line type="monotone" dataKey="sessions" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1' }} name="Sessions" />
      <Line type="monotone" dataKey="goals" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} name="Goals Achieved" />
      <Legend wrapperStyle={{ color: '#9ca3af' }} />
    </LineChart>
  </ResponsiveContainer>
);

export const ApprovalRateArea = ({ data }: { data: { period: string; approved: number; changes_requested: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <AreaChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
      <XAxis dataKey="period" tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
      <Area type="monotone" dataKey="approved" stackId="1" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} name="Approved" />
      <Area type="monotone" dataKey="changes_requested" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} name="Changes Requested" />
      <Legend wrapperStyle={{ color: '#9ca3af' }} />
    </AreaChart>
  </ResponsiveContainer>
);

export const MentorMenteeScatter = ({ data }: { data: { mentor: string; mentees: number; avgRating: number; sessions: number }[] }) => (
  <ResponsiveContainer width="100%" height={260}>
    <ScatterChart>
      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
      <XAxis type="category" dataKey="mentor" tick={{ fill: '#9ca3af', fontSize: 11 }} />
      <YAxis type="number" dataKey="avgRating" tick={{ fill: '#9ca3af', fontSize: 11 }} domain={[0, 5]} name="Rating" />
      <ZAxis type="number" dataKey="sessions" range={[200, 800]} name="Sessions" />
      <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
      <Scatter fill="#8b5cf6" />
    </ScatterChart>
  </ResponsiveContainer>
);
