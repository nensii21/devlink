import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { projectCommentsApi } from "../modules/projectComments";
import { api } from "../client";

const PROJECT_ID = "11111111-1111-4111-8111-111111111111";
const COMMENT_ID = "22222222-2222-4222-8222-222222222222";

describe("projectCommentsApi", () => {
  beforeEach(() => {
    vi.spyOn(api, "get").mockResolvedValue({} as never);
    vi.spyOn(api, "post").mockResolvedValue({} as never);
    vi.spyOn(api, "patch").mockResolvedValue({} as never);
    vi.spyOn(api, "delete").mockResolvedValue(undefined as never);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("list", () => {
    it("targets the project-scoped collection", async () => {
      await projectCommentsApi.list(PROJECT_ID);

      expect(api.get).toHaveBeenCalledWith(
        `/api/v1/projects/${PROJECT_ID}/comments`,
        expect.anything(),
      );
    });

    it("passes pagination through as query params", async () => {
      await projectCommentsApi.list(PROJECT_ID, { limit: 5, offset: 10 });

      expect(api.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ query: { limit: 5, offset: 10 } }),
      );
    });

    it("forwards an abort signal so a navigation can cancel the request", async () => {
      const controller = new AbortController();

      await projectCommentsApi.list(PROJECT_ID, {}, controller.signal);

      expect(api.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ signal: controller.signal }),
      );
    });
  });

  describe("count", () => {
    it("hits the count sub-resource", async () => {
      await projectCommentsApi.count(PROJECT_ID);

      expect(api.get).toHaveBeenCalledWith(
        `/api/v1/projects/${PROJECT_ID}/comments/count`,
        expect.anything(),
      );
    });
  });

  describe("create", () => {
    it("sends parent_id as null for a top-level comment", async () => {
      await projectCommentsApi.create(PROJECT_ID, { body: "Hello" });

      expect(api.post).toHaveBeenCalledWith(`/api/v1/projects/${PROJECT_ID}/comments`, {
        body: "Hello",
        parent_id: null,
      });
    });

    it("sends the parent id for a reply", async () => {
      await projectCommentsApi.create(PROJECT_ID, {
        body: "Answering",
        parent_id: COMMENT_ID,
      });

      expect(api.post).toHaveBeenCalledWith(expect.any(String), {
        body: "Answering",
        parent_id: COMMENT_ID,
      });
    });
  });

  describe("update", () => {
    it("patches the individual comment", async () => {
      await projectCommentsApi.update(PROJECT_ID, COMMENT_ID, {
        body: "Revised",
      });

      expect(api.patch).toHaveBeenCalledWith(
        `/api/v1/projects/${PROJECT_ID}/comments/${COMMENT_ID}`,
        { body: "Revised" },
      );
    });
  });

  describe("remove", () => {
    it("deletes the individual comment", async () => {
      await projectCommentsApi.remove(PROJECT_ID, COMMENT_ID);

      expect(api.delete).toHaveBeenCalledWith(
        `/api/v1/projects/${PROJECT_ID}/comments/${COMMENT_ID}`,
      );
    });
  });

  it("scopes every path to the given project", async () => {
    const other = "33333333-3333-4333-8333-333333333333";

    await projectCommentsApi.list(other);

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining(`/projects/${other}/`),
      expect.anything(),
    );
  });
});
