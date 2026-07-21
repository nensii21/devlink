export { api, ApiError, API_BASE_URL, isBackendConfigured } from "./client";
export { tokenStore } from "./tokens";
export { ws } from "./ws";
export type { WsEvent } from "./ws";

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
export { activitiesApi } from "./modules/activities";
export { collectionsApi } from "./modules/collections";
export type {
  BookmarkCollection,
  BookmarkCollectionWithBookmarks,
  Bookmark,
} from "./modules/collections";
