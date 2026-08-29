import React from 'react';
import type {
  Hackathon, Team, Submission, Judge, Award, HackathonInsight,
} from '../types';
import {
  HACKATHON_STATUS_COLORS, SUBMISSION_STATUS_COLORS, AWARD_TIER_COLORS,
  AWARD_TIER_ICONS, SCORE_CATEGORIES, formatNumber, formatCurrency, formatRelativeTime,
} from '../types';
import { Card } from '@/components/shared/primitives';
import { TypoCaption, TypoHeading } from '@/components/shared/Typography';

// ============================================================================
// HackathonCard
// ============================================================================

export function HackathonCard({ hackathon }: { hackathon: Hackathon }) {
  const statusColor = HACKATHON_STATUS_COLORS[hackathon.status];
  const progress = (hackathon.currentParticipants / hackathon.maxParticipants) * 100;

  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <TypoHeading level={5} className="font-semibold text-foreground">{hackathon.title}</TypoHeading>
          <TypoCaption className="text-muted-foreground text-xs">Theme: {hackathon.theme}</TypoCaption>
        </div>
        <span className="text-[10px] font-semibold px-2 py-1 rounded-full text-white" style={{ backgroundColor: statusColor }}>
          {hackathon.status}
        </span>
      </div>

      <TypoCaption className="text-muted-foreground text-xs block mb-3 line-clamp-2">{hackathon.description}</TypoCaption>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Duration</TypoCaption>
          <p className="text-xs font-medium text-foreground">{hackathon.isVirtual ? '💻 Virtual' : hackathon.location}</p>
        </div>
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Team Size</TypoCaption>
          <p className="text-xs font-medium text-foreground capitalize">{hackathon.teamSizeRange}</p>
        </div>
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Prizes</TypoCaption>
          <p className="text-xs font-medium text-yellow-500">{formatCurrency(hackathon.prizes[0]?.amount || 0)}</p>
        </div>
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Participants</TypoCaption>
          <p className="text-xs font-medium text-foreground">{hackathon.currentParticipants}/{hackathon.maxParticipants}</p>
        </div>
      </div>

      <div className="mb-3">
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        {hackathon.tracks.slice(0, 3).map(track => (
          <span key={track} className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{track}</span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <TypoCaption className="text-muted-foreground text-[10px]">by {hackathon.organizerName}</TypoCaption>
        <TypoCaption className="text-muted-foreground text-[10px]">Sponsors: {hackathon.sponsors.slice(0, 2).join(', ')}</TypoCaption>
      </div>
    </Card>
  );
}

// ============================================================================
// TeamCard
// ============================================================================

export function TeamCard({ team }: { team: Team }) {
  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200">
      <div className="flex items-start justify-between mb-2">
        <div>
          <TypoHeading level={5} className="font-semibold text-foreground">{team.name}</TypoHeading>
          <TypoCaption className="text-muted-foreground text-xs">{team.hackathonTitle}</TypoCaption>
        </div>
        {team.isOpen ? (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-green-500/20 text-green-500">🟢 Open</span>
        ) : (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">Full</span>
        )}
      </div>

      <TypoCaption className="text-muted-foreground text-xs block mb-3">{team.description}</TypoCaption>

      <div className="flex items-center gap-2 mb-3">
        {team.members.map(member => (
          <div key={member.id} className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-[10px] font-bold" title={`${member.name} (${member.role})`}>
            {member.name.split(' ').map(n => n[0]).join('')}
          </div>
        ))}
        <TypoCaption className="text-muted-foreground text-[10px]">{team.members.length}/{team.maxMembers} members</TypoCaption>
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        {team.neededSkills.map(skill => (
          <span key={skill} className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500 font-medium">Need: {skill}</span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <TypoCaption className="text-muted-foreground text-[10px]">Created {formatRelativeTime(team.createdAt)}</TypoCaption>
        {team.hasSubmission && <span className="text-[10px] font-semibold text-green-500">✅ Submitted</span>}
      </div>
    </Card>
  );
}

// ============================================================================
// SubmissionCard
// ============================================================================

export function SubmissionCard({ submission }: { submission: Submission }) {
  const statusColor = SUBMISSION_STATUS_COLORS[submission.status];

  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          <TypoHeading level={5} className="font-semibold text-foreground">{submission.title}</TypoHeading>
          <TypoCaption className="text-muted-foreground text-xs">by {submission.teamName}</TypoCaption>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: statusColor }}>
            {submission.status}
          </span>
          {submission.totalScore > 0 && (
            <span className="text-sm font-bold text-yellow-500">{submission.totalScore}/50</span>
          )}
        </div>
      </div>

      <TypoCaption className="text-muted-foreground text-xs block mb-3">{submission.description}</TypoCaption>

      <div className="grid grid-cols-5 gap-1 mb-3">
        {submission.scores.map(score => {
          const cat = SCORE_CATEGORIES.find(c => c.key === score.category);
          return (
            <div key={score.category} className="text-center">
              <TypoCaption className="text-muted-foreground text-[9px]">{cat?.icon}</TypoCaption>
              <p className="text-xs font-semibold text-foreground">{score.score}</p>
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        {submission.techStack.slice(0, 4).map(tech => (
          <span key={tech} className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{tech}</span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <TypoCaption className="text-muted-foreground text-[10px]">Track: {submission.track}</TypoCaption>
        {submission.demoUrl && <TypoCaption className="text-primary text-[10px]">🔗 Demo</TypoCaption>}
      </div>
    </Card>
  );
}

// ============================================================================
// JudgeCard
// ============================================================================

export function JudgeCard({ judge }: { judge: Judge }) {
  return (
    <Card className="p-3 hover:shadow-lg transition-all duration-200">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-bold">
          {judge.name.split(' ').map(n => n[0]).join('')}
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">{judge.name}</p>
          <TypoCaption className="text-muted-foreground text-[10px]">{judge.title} @ {judge.company}</TypoCaption>
        </div>
      </div>
      <div className="flex flex-wrap gap-1 mb-2">
        {judge.expertise.map(exp => (
          <span key={exp} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{exp}</span>
        ))}
      </div>
      <div className="flex justify-between">
        <TypoCaption className="text-muted-foreground text-[10px]">Scores: {judge.scoreCount}</TypoCaption>
        <TypoCaption className="text-foreground text-[10px] font-medium">Avg: {judge.avgScore}/10</TypoCaption>
      </div>
    </Card>
  );
}

// ============================================================================
// AwardCard
// ============================================================================

export function AwardCard({ award }: { award: Award }) {
  const tierColor = AWARD_TIER_COLORS[award.tier];
  const tierIcon = AWARD_TIER_ICONS[award.tier];

  return (
    <Card className="p-3 hover:shadow-lg transition-all duration-200" style={{ borderLeft: `3px solid ${tierColor}` }}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{tierIcon}</span>
        <div className="flex-1">
          <TypoHeading level={5} className="font-semibold text-foreground text-sm">{award.title}</TypoHeading>
          <TypoCaption className="text-muted-foreground text-[10px]">{award.description}</TypoCaption>
        </div>
        <span className="text-sm font-bold" style={{ color: tierColor }}>{formatCurrency(award.prize)}</span>
      </div>
      <TypoCaption className="text-muted-foreground text-[10px]">Team: <span className="text-foreground font-medium">{award.teamName}</span> — {award.submissionTitle}</TypoCaption>
    </Card>
  );
}

// ============================================================================
// InsightCard
// ============================================================================

export function InsightCard({ insight }: { insight: HackathonInsight }) {
  const typeConfig: Record<string, { color: string; icon: string }> = {
    success: { color: '#4caf50', icon: '✅' },
    warning: { color: '#ff9800', icon: '⚠️' },
    tip: { color: '#00e5ff', icon: '💡' },
    info: { color: '#9c27b0', icon: 'ℹ️' },
  };
  const config = typeConfig[insight.type];

  return (
    <Card className="p-3 hover:shadow-lg transition-all duration-200" style={{ borderLeft: `3px solid ${config.color}` }}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{config.icon}</span>
        <TypoHeading level={5} className="font-semibold text-foreground flex-1 text-sm">{insight.title}</TypoHeading>
        {insight.actionable && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/15 text-primary font-medium">Actionable</span>
        )}
      </div>
      <TypoCaption className="text-muted-foreground block mb-1">{insight.description}</TypoCaption>
      {insight.metric && (
        <TypoCaption className="text-muted-foreground">{insight.metric}: <span className="text-foreground font-medium">{insight.value}</span></TypoCaption>
      )}
    </Card>
  );
}
