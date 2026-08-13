import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { organizationsApi } from "../modules/organizations";
import { api } from "../client";

const ORG_ID = "11111111-1111-4111-8111-111111111111";

describe("organizationsApi (#958)", () => {
  beforeEach(() => {
    vi.spyOn(api, "get").mockResolvedValue({} as never);
    vi.spyOn(api, "put").mockResolvedValue({} as never);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("get", () => {
    it("fetches a single organization", async () => {
      await organizationsApi.get(ORG_ID);

      expect(api.get).toHaveBeenCalledWith(`/api/v1/organizations/${ORG_ID}`);
    });

    it("URL-encodes the organization id", async () => {
      await organizationsApi.get("org/with/slash");

      expect(api.get).toHaveBeenCalledWith("/api/v1/organizations/org%2Fwith%2Fslash");
    });
  });

  describe("list", () => {
    it("lists organizations", async () => {
      await organizationsApi.list();

      expect(api.get).toHaveBeenCalledWith("/api/v1/organizations");
    });
  });

  describe("listMine", () => {
    it("lists organizations owned by the current user", async () => {
      await organizationsApi.listMine();

      expect(api.get).toHaveBeenCalledWith("/api/v1/organizations/me");
    });
  });

  describe("update", () => {
    it("PUTs branding updates to the organization", async () => {
      await organizationsApi.update(ORG_ID, {
        logo_url: "https://example.com/new-logo.png",
        banner_url: undefined,
      });

      expect(api.put).toHaveBeenCalledWith(`/api/v1/organizations/${ORG_ID}`, {
        logo_url: "https://example.com/new-logo.png",
        banner_url: undefined,
      });
    });

    it("supports clearing a field with null", async () => {
      await organizationsApi.update(ORG_ID, { banner_url: null });

      expect(api.put).toHaveBeenCalledWith(`/api/v1/organizations/${ORG_ID}`, { banner_url: null });
    });
  });
});
