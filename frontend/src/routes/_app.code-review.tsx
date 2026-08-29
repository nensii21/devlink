import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import {
  reviews, mentorshipSessions, reviewMetrics, mentorshipMetrics,
  mentors, responseTimeDistribution, languageReviewStats, reviewTimeline,
  qualityCategories, mentorshipTimeline, approvalRateTrend
} from '../features/codeReview/service';
import { calculateReviewStats } from '../features/codeReview/types';
import type { ReviewFilterStatus } from '../features/codeReview/types';
import {
  ReviewQualityRadar, ReviewVolumeBar, ResponseTimeBar, LanguagePie,
  MentorshipProgressLine, ApprovalRateArea, MentorMenteeScatter
} from '../features/codeReview/components/CodeReviewCharts';

export const Route = createFileRoute('/_app/code-review')({
  component: CodeReviewPage,
});

function CodeReviewPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [statusFilter, setStatusFilter] = useState<ReviewFilterStatus>('all');
  const stats = calculateReviewStats(reviews);

  const filteredReviews = statusFilter === 'all'
    ? reviews
    : reviews.filter(r => r.status === statusFilter);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'reviews', label: 'Code Reviews' },
    { id: 'comments', label: 'Comments & Feedback' },
    { id: 'mentorship', label: 'Mentorship' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'insights', label: 'Insights' },
  ];

  const statusColors: Record<string, string> = {
    open: 'text-blue-400', in_review: 'text-yellow-400', approved: 'text-green-400',
    changes_requested: 'text-orange-400', merged: 'text-purple-400', closed: 'text-gray-400',
  };

  const priorityColors: Record<string, string> = {
    low: 'border-green-500/30', medium: 'border-yellow-500/30', high: 'border-orange-500/30', critical: 'border-red-500/30',
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            📝 Code Review & Mentorship
          </h1>
          <p className="text-gray-400 mt-2">Collaborative code review tracking and mentorship program management</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-800/50 rounded-xl p-1 backdrop-blur-sm overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Total Reviews', value: reviewMetrics.totalReviews, icon: '🔍' },
                { label: 'Avg Response Time', value: reviewMetrics.averageResponseTime, icon: '⚡' },
                { label: 'Approval Rate', value: `${reviewMetrics.approvalRate}%`, icon: '✅' },
                { label: 'Active Mentorships', value: mentorshipMetrics.activeMentorships, icon: '🎓' },
              ].map((kpi, i) => (
                <div key={i} className="bg-gray-800/60 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
                  <div className="text-2xl mb-1">{kpi.icon}</div>
                  <div className="text-2xl font-bold text-white">{kpi.value}</div>
                  <div className="text-sm text-gray-400">{kpi.label}</div>
                </div>
              ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800/60 backdrop-blur-sm rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4 text-white">📈 Review Volume (7 Days)</h3>
                <ReviewVolumeBar data={reviewTimeline} />
              </div>
              <div className="bg-gray-800/60 backdrop-blur-sm rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4 text-white">🎯 Quality Categories</h3>
                <ReviewQualityRadar data={qualityCategories} />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800/60 backdrop-blur-sm rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4 text-white">⏱️ Response Time Distribution</h3>
                <ResponseTimeBar data={responseTimeDistribution} />
              </div>
              <div className="bg-gray-800/60 backdrop-blur-sm rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4 text-white">📊 Approval vs Changes</h3>
                <ApprovalRateArea data={approvalRateTrend} />
              </div>
            </div>

            {/* Review Status Summary */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                { label: 'Open', count: stats.openReviews, color: 'bg-blue-500' },
                { label: 'In Review', count: stats.inReviewCount, color: 'bg-yellow-500' },
                { label: 'Approved', count: stats.approvedReviews, color: 'bg-green-500' },
                { label: 'Changes Requested', count: stats.changesRequested, color: 'bg-orange-500' },
                { label: 'Merged', count: stats.mergedReviews, color: 'bg-purple-500' },
              ].map((s, i) => (
                <div key={i} className="bg-gray-800/60 rounded-lg p-3 border border-gray-700/50 text-center">
                  <div className={`text-2xl font-bold text-white`}>{s.count}</div>
                  <div className="text-xs text-gray-400 mt-1">{s.label}</div>
                  <div className={`h-1 ${s.color} rounded-full mt-2 opacity-60`}></div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reviews Tab */}
        {activeTab === 'reviews' && (
          <div className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              {['all', 'open', 'in_review', 'approved', 'changes_requested', 'merged'].map(status => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status as ReviewFilterStatus)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    statusFilter === status
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {status === 'all' ? 'All' : status.replace('_', ' ')}
                  {status !== 'all' && (
                    <span className="ml-1 text-xs opacity-60">({reviews.filter(r => r.status === status).length})</span>
                  )}
                </button>
              ))}
            </div>

            <div className="space-y-3">
              {filteredReviews.map(review => (
                <div key={review.id} className={`bg-gray-800/60 backdrop-blur-sm rounded-xl p-5 border ${priorityColors[review.priority]} hover:border-indigo-500/50 transition-all`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`font-semibold text-white`}>{review.title}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[review.status]} bg-gray-700/50`}>
                          {review.status.replace('_', ' ')}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700/50 text-gray-300">{review.priority}</span>
                      </div>
                      <p className="text-sm text-gray-400 mb-2">{review.description}</p>
                      <div className="flex flex-wrap gap-2 mb-2">
                        <span className="text-xs bg-gray-700/50 px-2 py-1 rounded text-gray-300">📁 {review.repository}</span>
                        <span className="text-xs bg-gray-700/50 px-2 py-1 rounded text-gray-300">{review.language}</span>
                        {review.filesChanged.map(f => (
                          <span key={f} className="text-xs bg-indigo-900/30 px-2 py-1 rounded text-indigo-300">{f}</span>
                        ))}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>👤 {review.author.name}</span>
                        <span>📅 {review.submittedAt.toLocaleDateString()}</span>
                        <span>💬 {review.comments.length} comments</span>
                        <span>📊 {review.linesChanged} lines changed</span>
                        <span>✅ {review.approvals}/{review.requiredApprovals} approvals</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comments Tab */}
        {activeTab === 'comments' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-green-400">{reviewMetrics.totalComments}</div>
                <div className="text-xs text-gray-400">Total Comments</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-blue-400">{reviewMetrics.codeSuggestions}</div>
                <div className="text-xs text-gray-400">Code Suggestions</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-purple-400">{reviewMetrics.averageCommentsPerReview}</div>
                <div className="text-xs text-gray-400">Avg Comments/Review</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-yellow-400">{reviewMetrics.conversationsResolved}/{reviewMetrics.totalConversations}</div>
                <div className="text-xs text-gray-400">Conversations Resolved</div>
              </div>
            </div>

            <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
              <h3 className="text-lg font-semibold mb-4">Recent Comments</h3>
              <div className="space-y-3">
                {reviews.flatMap(r => r.comments.slice(0, 2).map(c => ({ ...c, reviewTitle: r.title, file: r.filesChanged[0] }))).slice(0, 8).map(comment => (
                  <div key={comment.id} className="border-l-2 border-indigo-500/50 pl-4 py-2">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-white">{comment.author.name}</span>
                      <span className="text-xs text-gray-500">{comment.author.role}</span>
                      <span className="text-xs text-gray-600">on {comment.file}</span>
                      <span className="text-xs text-gray-600">• {comment.createdAt.toLocaleDateString()}</span>
                    </div>
                    <p className="text-sm text-gray-300">{comment.content}</p>
                    {comment.suggestion && (
                      <div className="mt-2 bg-gray-900/50 rounded-lg p-2 text-xs font-mono text-green-400">
                        💡 {comment.suggestion}
                      </div>
                    )}
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span>👍 {comment.reactions.thumbsUp}</span>
                      <span>👎 {comment.reactions.thumbsDown}</span>
                      <span>❤️ {comment.reactions.heart}</span>
                      <span>{comment.resolved ? '✅ Resolved' : '⏳ Open'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Mentorship Tab */}
        {activeTab === 'mentorship' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-indigo-400">{mentorshipMetrics.activeMentorships}</div>
                <div className="text-xs text-gray-400">Active Mentorships</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-green-400">{mentorshipMetrics.completedSessions}</div>
                <div className="text-xs text-gray-400">Completed Sessions</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-yellow-400">{mentorshipMetrics.goalsAchieved}/{mentorshipMetrics.totalGoals}</div>
                <div className="text-xs text-gray-400">Goals Achieved</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-purple-400">{mentorshipMetrics.satisfactionScore}/5</div>
                <div className="text-xs text-gray-400">Satisfaction Score</div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4">📈 Mentorship Progress</h3>
                <MentorshipProgressLine data={mentorshipTimeline} />
              </div>
              <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4">🎯 Mentor Effectiveness</h3>
                <MentorMenteeScatter data={mentors} />
              </div>
            </div>

            {/* Mentorship Sessions */}
            <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
              <h3 className="text-lg font-semibold mb-4">🎓 Mentorship Sessions</h3>
              <div className="space-y-3">
                {mentorshipSessions.map(session => (
                  <div key={session.id} className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-white">{session.mentor.name} → {session.mentee.name}</div>
                      <div className="text-xs text-gray-400">{session.topic} • {session.duration}min • {session.type}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-400">{session.date.toLocaleDateString()}</div>
                      {session.rating && <div className="text-xs text-yellow-400">⭐ {session.rating}/5</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4">📊 Approval Rate Trend</h3>
                <ApprovalRateArea data={approvalRateTrend} />
              </div>
              <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4">🌐 Language Distribution</h3>
                <LanguagePie data={languageReviewStats} />
              </div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4">⏱️ Response Time Distribution</h3>
                <ResponseTimeBar data={responseTimeDistribution} />
              </div>
              <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
                <h3 className="text-lg font-semibold mb-4">📈 Review Volume</h3>
                <ReviewVolumeBar data={reviewTimeline} />
              </div>
            </div>
            {/* Metrics Table */}
            <div className="bg-gray-800/60 rounded-xl p-5 border border-gray-700/50">
              <h3 className="text-lg font-semibold mb-4">📋 Detailed Metrics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(reviewMetrics).filter(([k]) => !k.includes('resolution') || k.includes('resolutionTime')).map(([key, value]) => (
                  <div key={key} className="bg-gray-900/50 rounded-lg p-3">
                    <div className="text-sm font-medium text-white">{String(value)}</div>
                    <div className="text-xs text-gray-400 capitalize">{key.replace(/([A-Z])/g, ' $1')}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Insights Tab */}
        {activeTab === 'insights' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-green-400">{reviewMetrics.totalApprovalRate}%</div>
                <div className="text-xs text-gray-400">Overall Approval Rate</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-indigo-400">{mentorshipMetrics.improvementRate}%</div>
                <div className="text-xs text-gray-400">Mentee Improvement Rate</div>
              </div>
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50 text-center">
                <div className="text-2xl font-bold text-purple-400">{reviewMetrics.automationRate}%</div>
                <div className="text-xs text-gray-400">Automation Rate</div>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-semibold">💡 AI-Generated Insights</h3>
              {reviewMetrics.insights.map((insight, i) => (
                <div key={i} className={`bg-gray-800/60 rounded-xl p-5 border-l-4 ${
                  insight.type === 'positive' ? 'border-green-500' :
                  insight.type === 'warning' ? 'border-yellow-500' :
                  insight.type === 'negative' ? 'border-red-500' : 'border-indigo-500'
                }`}>
                  <div className="flex items-start gap-3">
                    <span className="text-xl">
                      {insight.type === 'positive' ? '✅' : insight.type === 'warning' ? '⚠️' : insight.type === 'negative' ? '🔴' : '💡'}
                    </span>
                    <div>
                      <div className="font-medium text-white">{insight.title}</div>
                      <p className="text-sm text-gray-400 mt-1">{insight.description}</p>
                      <div className="mt-2 text-xs text-indigo-400">Action: {insight.action}</div>
                      <div className="text-xs text-gray-500 mt-1">Impact: {insight.impact}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
