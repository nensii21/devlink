import React from 'react';
import type {
  CodeReview, FeedbackItem, MentorProfile, MentorMatch,
  MentorshipSession, CodeReviewInsight,
} from '../types';
import {
  REVIEW_STATUS_COLORS, REVIEW_TYPE_ICONS, SEVERITY_COLORS, SEVERITY_ICONS,
  MATCH_SCORE_COLORS, FOCUS_ICONS, STATUS_COLORS,
  formatRelativeTime,
} from '../types';
import { Card } from '@/components/shared/primitives';
import { TypoCaption, TypoHeading } from '@/components/shared/Typography';

// ============================================================================
// ReviewCard
// ============================================================================

export function ReviewCard({ review }: { review: CodeReview }) {
  const statusColor = REVIEW_STATUS_COLORS[review.status];
  const typeIcon = REVIEW_TYPE_ICONS[review.type];

  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{typeIcon}</span>
          <div className="flex-1">
            <TypoHeading level={5} className="font-semibold text-foreground">{review.title}</TypoHeading>
            <TypoCaption className="text-muted-foreground text-xs">{review.fileCount} files · {review.linesChanged} lines changed</TypoCaption>
          </div>
        </div>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: statusColor }}>
          {review.status}
        </span>
      </div>

      <TypoCaption className="text-muted-foreground text-xs block mb-3">{review.description}</TypoCaption>

      {review.qualityScore > 0 && (
        <div className="mb-3">
          <div className="flex justify-between mb-1">
            <TypoCaption className="text-muted-foreground text-[10px]">Quality Score</TypoCaption>
            <TypoCaption className="text-foreground text-[10px] font-medium">{review.qualityScore}/100</TypoCaption>
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${review.qualityScore}%`, backgroundColor: review.qualityScore >= 80 ? '#4caf50' : review.qualityScore >= 60 ? '#ff9800' : '#f44336' }} />
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 mb-2">
        <TypoCaption className="text-muted-foreground text-[10px]">by {review.author}</TypoCaption>
        {review.reviewer && <TypoCaption className="text-muted-foreground text-[10px]">→ {review.reviewer}</TypoCaption>}
      </div>

      <div className="flex flex-wrap gap-1 mb-2">
        {Object.entries(review.severityBreakdown).filter(([_, count]) => count > 0).map(([sev, count]) => (
          <span key={sev} className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${SEVERITY_COLORS[sev as keyof typeof SEVERITY_COLORS]}20`, color: SEVERITY_COLORS[sev as keyof typeof SEVERITY_COLORS] }}>
            {SEVERITY_ICONS[sev as keyof typeof SEVERITY_ICONS]} {count}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <TypoCaption className="text-muted-foreground text-[10px]">{review.feedbackCount} feedback items</TypoCaption>
        <TypoCaption className="text-muted-foreground text-[10px]">{formatRelativeTime(review.submittedAt)}</TypoCaption>
      </div>
    </Card>
  );
}

// ============================================================================
// FeedbackCard
// ============================================================================

export function FeedbackCard({ feedback }: { feedback: FeedbackItem }) {
  const sevColor = SEVERITY_COLORS[feedback.severity];
  const sevIcon = SEVERITY_ICONS[feedback.severity];

  return (
    <Card className="p-3 hover:shadow-lg transition-all duration-200" style={{ borderLeft: `3px solid ${sevColor}` }}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm">{sevIcon}</span>
        <TypoCaption className="text-foreground text-xs font-medium">{feedback.category}</TypoCaption>
        <TypoCaption className="text-muted-foreground text-[10px] ml-auto">{feedback.file}:{feedback.line}</TypoCaption>
        {feedback.resolved && <span className="text-[10px] text-green-500">✅</span>}
      </div>
      <TypoCaption className="text-foreground text-xs block mb-1">{feedback.message}</TypoCaption>
      {feedback.suggestion && (
        <TypoCaption className="text-primary text-[10px] block mb-1">💡 {feedback.suggestion}</TypoCaption>
      )}
      <TypoCaption className="text-muted-foreground text-[10px]">— {feedback.author} · {formatRelativeTime(feedback.createdAt)}</TypoCaption>
    </Card>
  );
}

// ============================================================================
// MentorCard
// ============================================================================

export function MentorCard({ mentor }: { mentor: MentorProfile }) {
  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200">
      <div className="flex items-start gap-3 mb-2">
        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary text-sm font-bold flex-shrink-0">
          {mentor.name.split(' ').map(n => n[0]).join('')}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <TypoHeading level={5} className="font-semibold text-foreground">{mentor.name}</TypoHeading>
            {mentor.available ? <span className="w-2 h-2 rounded-full bg-green-500" /> : <span className="w-2 h-2 rounded-full bg-red-500" />}
          </div>
          <TypoCaption className="text-muted-foreground text-xs">{mentor.title} @ {mentor.company}</TypoCaption>
        </div>
      </div>

      <TypoCaption className="text-muted-foreground text-xs block mb-2">{mentor.bio}</TypoCaption>

      <div className="flex flex-wrap gap-1 mb-2">
        {mentor.expertise.map(exp => (
          <span key={exp} className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{exp}</span>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Rating</TypoCaption>
          <p className="text-xs font-semibold text-yellow-500">⭐ {mentor.rating}</p>
        </div>
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Reviews</TypoCaption>
          <p className="text-xs font-semibold text-foreground">{mentor.reviewCount}</p>
        </div>
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Mentees</TypoCaption>
          <p className="text-xs font-semibold text-foreground">{mentor.currentMentees}/{mentor.maxMentees}</p>
        </div>
        <div>
          <TypoCaption className="text-muted-foreground text-[10px]">Response</TypoCaption>
          <p className="text-xs font-semibold text-foreground">{mentor.responseTime}</p>
        </div>
      </div>

      <div className="pt-2 border-t border-border">
        {mentor.available ? (
          <button className="text-[10px] font-semibold px-3 py-1 rounded-full bg-primary text-primary-foreground">Request Mentorship</button>
        ) : (
          <TypoCaption className="text-muted-foreground text-[10px]">Currently at capacity</TypoCaption>
        )}
      </div>
    </Card>
  );
}

// ============================================================================
// MatchCard
// ============================================================================

export function MatchCard({ match }: { match: MentorMatch }) {
  const matchColor = MATCH_SCORE_COLORS[match.matchScore];

  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200" style={{ borderLeft: `3px solid ${matchColor}` }}>
      <div className="flex items-center justify-between mb-2">
        <TypoHeading level={5} className="font-semibold text-foreground">{match.mentor.name}</TypoHeading>
        <span className="text-sm font-bold" style={{ color: matchColor }}>{match.matchPercentage}%</span>
      </div>
      <TypoCaption className="text-muted-foreground text-xs block mb-2">{match.mentor.title} @ {match.mentor.company}</TypoCaption>

      <div className="mb-2">
        <div className="h-2 rounded-full bg-muted overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${match.matchPercentage}%`, backgroundColor: matchColor }} />
        </div>
      </div>

      <div className="space-y-1 mb-2">
        {match.matchReasons.map((reason, i) => (
          <TypoCaption key={i} className="text-muted-foreground text-[10px] block">✓ {reason}</TypoCaption>
        ))}
      </div>

      <div className="flex flex-wrap gap-1">
        {match.focusAreas.map(focus => (
          <span key={focus} className="text-[10px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
            {FOCUS_ICONS[focus]} {focus}
          </span>
        ))}
      </div>
    </Card>
  );
}

// ============================================================================
// SessionCard
// ============================================================================

export function SessionCard({ session }: { session: MentorshipSession }) {
  const statusColor = STATUS_COLORS[session.status];
  const progress = (session.sessionsCompleted / session.totalSessions) * 100;

  return (
    <Card className="p-4 hover:shadow-lg transition-all duration-200">
      <div className="flex items-center justify-between mb-2">
        <div>
          <TypoHeading level={5} className="font-semibold text-foreground">{session.mentorName}</TypoHeading>
          <TypoCaption className="text-muted-foreground text-xs capitalize">{session.focus} mentorship</TypoCaption>
        </div>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full text-white" style={{ backgroundColor: statusColor }}>
          {session.status}
        </span>
      </div>

      <div className="mb-3">
        <div className="flex justify-between mb-1">
          <TypoCaption className="text-muted-foreground text-[10px]">Sessions</TypoCaption>
          <TypoCaption className="text-foreground text-[10px]">{session.sessionsCompleted}/{session.totalSessions}</TypoCaption>
        </div>
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <div className="h-full rounded-full bg-primary" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="space-y-1 mb-2">
        {session.goals.slice(0, 3).map((goal, i) => (
          <TypoCaption key={i} className="text-muted-foreground text-[10px] block">• {goal}</TypoCaption>
        ))}
      </div>

      {session.nextSession && (
        <TypoCaption className="text-primary text-[10px] block mb-1">📅 Next: {new Date(session.nextSession).toLocaleString()}</TypoCaption>
      )}
      {session.rating && (
        <TypoCaption className="text-yellow-500 text-[10px]">⭐ {session.rating}/5</TypoCaption>
      )}
    </Card>
  );
}

// ============================================================================
// InsightCard
// ============================================================================

export function InsightCard({ insight }: { insight: CodeReviewInsight }) {
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
