import React from 'react';
import type { Submission, Hackathon, Award } from '../types';
import { Card } from '@/components/shared/primitives';
import { TypoHeading } from '@/components/shared/Typography';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';

// ============================================================================
// SubmissionScoresRadar — radar chart of a submission's scores across categories
// ============================================================================

export function SubmissionScoresRadar({ submission, title }: { submission: Submission; title: string }) {
  const radarData = submission.scores.map(s => ({
    category: s.category,
    score: s.score,
    fullMark: s.maxScore,
  }));

  return (
    <Card className="p-4">
      <TypoHeading level={5} className="font-semibold text-foreground mb-4">{title}</TypoHeading>
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis dataKey="category" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }} />
          <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 9 }} />
          <Radar name="Score" dataKey="score" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.25} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </Card>
  );
}

// ============================================================================
// PrizePie — donut chart of prize distribution
// ============================================================================

export function PrizePie({ hackathon, title }: { hackathon: Hackathon; title: string }) {
  const colors = ['#ffd700', '#c0c0c0', '#cd7f32', '#9c27b0', '#2196f3'];
  const total = hackathon.prizes.reduce((s, p) => s + p.amount, 0);

  const pieData = hackathon.prizes.map((p, i) => ({
    name: p.tier,
    value: p.amount,
    color: colors[i % colors.length],
  }));

  return (
    <Card className="p-4">
      <TypoHeading level={5} className="font-semibold text-foreground mb-4">{title}</TypoHeading>
      <div className="flex items-center justify-center gap-6">
        <ResponsiveContainer width="40%" height={180}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={4} dataKey="value">
              {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }} formatter={(value: number) => [`$${value.toLocaleString()}`, 'Prize']} />
          </PieChart>
        </ResponsiveContainer>
        <div className="space-y-2">
          {pieData.map(d => (
            <div key={d.name} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
              <TypoCaption className="text-foreground text-xs capitalize">{d.name}</TypoCaption>
              <TypoCaption className="text-muted-foreground text-xs ml-auto">${d.value.toLocaleString()}</TypoCaption>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

// ============================================================================
// ParticipationBar — bar chart of hackathon participation
// ============================================================================

export function ParticipationBar({ hackathons, title }: { hackathons: Hackathon[]; title: string }) {
  const data = hackathons.map(h => ({
    name: h.title.substring(0, 15),
    participants: h.currentParticipants,
    capacity: h.maxParticipants,
  }));

  return (
    <Card className="p-4">
      <TypoHeading level={5} className="font-semibold text-foreground mb-4">{title}</TypoHeading>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="name" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 9 }} angle={-15} textAnchor="end" />
          <YAxis tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }} />
          <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }} />
          <Bar dataKey="participants" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="Registered" />
          <Bar dataKey="capacity" fill="hsl(var(--muted))" radius={[4, 4, 0, 0]} name="Capacity" opacity={0.3} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

// ============================================================================
// ScoreComparison — bar chart comparing top submissions
// ============================================================================

export function ScoreComparison({ submissions, title }: { submissions: Submission[]; title: string }) {
  const data = submissions
    .filter(s => s.totalScore > 0)
    .sort((a, b) => b.totalScore - a.totalScore)
    .slice(0, 5)
    .map(s => ({
      name: s.title.substring(0, 12),
      score: s.totalScore,
      innovation: s.scores.find(sc => sc.category === 'innovation')?.score || 0,
      technical: s.scores.find(sc => sc.category === 'technical')?.score || 0,
    }));

  return (
    <Card className="p-4">
      <TypoHeading level={5} className="font-semibold text-foreground mb-4">{title}</TypoHeading>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="name" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }} />
          <YAxis domain={[0, 50]} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }} />
          <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }} />
          <Bar dataKey="score" fill="#ffd700" radius={[4, 4, 0, 0]} name="Total Score" />
          <Bar dataKey="innovation" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="Innovation" />
          <Bar dataKey="technical" fill="#4caf50" radius={[4, 4, 0, 0]} name="Technical" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
