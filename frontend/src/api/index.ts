export { api, ApiError, API_BASE_URL, isBackendConfigured } from "./client";
export { tokenStore } from "./tokens";
export { ws } from "./ws";
export type { CollabEvent as WsEvent } from "./ws";

export { authApi } from "./modules/auth";
export { usersApi } from "./modules/users";
export { projectsApi } from "./modules/projects";
export { buildersApi } from "./modules/builders";
export { postsApi } from "./modules/posts";
export { messagesApi } from "./modules/messages";
export { notificationsApi } from "./modules/notifications";
export { analyticsApi } from "./modules/analytics";
export { hackathonsApi } from "./modules/hackathons";
export { searchApi } from "./modules/search";
export type {
  SearchCategory,
  SearchQuery,
  SearchAutocompleteResponse,
  SearchResponse,
  SearchCounts,
  SearchResultUser,
  SearchResultProject,
  SearchResultOrganization,
  SearchResultSkill,
  SearchResultTag,
  SearchSuggestionUser,
  SearchSuggestionProject,
  SearchSuggestionOrganization,
  SearchSuggestionSkill,
  SearchSuggestionTag,
  SEARCH_CATEGORIES,
} from "./modules/search";
export { activitiesApi } from "./modules/activities";
export { activityHeatmapApi } from "./modules/activityHeatmap";
export type {
  ActivityHeatmap,
  ActivityTypeCount,
  HeatmapDay,
  StreakSummary,
} from "./modules/activityHeatmap";
export { collectionsApi } from "./modules/collections";
export { recommendationsApi, fallbackTechStack } from "./modules/recommendations";
export type { TechStackRecommendation, TechStackResponse } from "./modules/recommendations";
export { bookmarksApi } from "./modules/bookmarks";
export { pinnedProjectsApi, MAX_PINNED_PROJECTS } from "./modules/pinnedProjects";
export type {
  PinnedProject,
  PinnedProjectList,
  PinnedProjectSummary,
} from "./modules/pinnedProjects";
export { issuesApi } from "./modules/issues";
export type {
  Issue,
  DifficultyEstimateResponse,
  IssueCreateInput,
  IssueUpdateInput,
} from "./modules/issues";
export { profileSummaryApi } from "./modules/profileSummary";
export type { ProfileSummaryResponse } from "./modules/profileSummary";
export { conversationStartersApi } from "./modules/conversationStarters";
export type { ConversationStarterResponse } from "./modules/conversationStarters";
export { projectTagsApi } from "./modules/projectTags";
export type { ProjectTagResponse } from "./modules/projectTags";

export { projectCommentsApi } from "./modules/projectComments";
export type {
  CommentAuthor,
  ProjectComment,
  ProjectCommentThread,
  ProjectCommentList,
  ListCommentsParams,
  CreateCommentPayload,
  UpdateCommentPayload,
} from "./modules/projectComments";
export { teamMatchApi } from "./modules/teamMatch";
export { contributorMatchingApi } from "./modules/contributorMatching";
export type { ContributorMatchResponse, MatchedContributor } from "./modules/contributorMatching";
export { reputationApi } from "./modules/reputation";
export type {
  ReputationLog,
  ReputationSummary,
  LeaderboardEntry,
  LeaderboardResponse,
  AwardReputationInput,
} from "./modules/reputation";
export { repositoryQualityApi } from "./modules/repositoryQuality";
export type {
  RepositoryQualityResponse,
  MetricScore,
  ImprovementSuggestion,
  RepositoryInfo,
} from "./modules/repositoryQuality";
export { exportApi } from "./modules/export";
export type { UserExportData, ExportResponse } from "./modules/export";
export { auditApi } from "./modules/audit";
export type { AuditLog, AuditLogQuery } from "./modules/audit";
export type {
  BookmarkResponse as BookmarkItem,
  BookmarkCheckResponse,
  BookmarkCountResponse,
} from "./modules/bookmarks";
export type {
  BookmarkCollection,
  BookmarkCollectionWithBookmarks,
  Bookmark,
} from "./modules/collections";
export type { TeamMatchRequest, TeamMatchResponse } from "./modules/teamMatch";
export { projectInsightsApi } from "./modules/projectInsights";
export type {
  ProjectInsightsResponse,
  ProjectInsightsRequest,
  SuggestedBuilder,
  RoleGap,
  RiskAlert,
} from "./modules/projectInsights";
export { sessionsApi } from "./modules/sessions";
export type { UserSession, RevokeSessionResponse } from "./modules/sessions";
export { projectTemplatesApi } from "./modules/projectTemplates";
export type {
  ProjectTemplate,
  ProjectTemplateListResponse,
  ProjectTemplateCreateInput,
} from "./modules/projectTemplates";
export { skillsApi } from "./modules/skills";
export type {
  SkillItem,
  SkillMatrixResponse,
  SkillSearchResult,
} from "./modules/skills";
export { dashboardLayoutApi } from "./modules/dashboardLayout";
export type {
  DashboardWidgetLayout,
  DashboardLayoutResponse,
} from "./modules/dashboardLayout";
export type { PlatformSocialProofResponse } from "./modules/analytics";
export { featureAnnouncementsApi } from "./modules/featureAnnouncements";
export type {
  FeatureAnnouncement,
  FeatureAnnouncementListResponse,
  CreateAnnouncementInput,
  AnnouncementCategory,
} from "./modules/featureAnnouncements";

