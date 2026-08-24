// Regression cover for #1315.
//
// The settings page is the only caller of `usersService.getMe`, and it was
// calling a method that did not exist. `updateMe` did exist and was worse: it
// was wrapped in `withFallback`, so every failure -- including the 409 that
// optimistic concurrency exists to produce -- came back as a truthy `{}` and
// was reported to the user as a successful save.
//
// These tests pin both halves at the service boundary, which is where the
// decision lives. The page-level consequence is covered in
// `components/__tests__/settings-profile.test.tsx`.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const PROFILE = {
  id: "usr_1",
  first_name: "Ada",
  last_name: "Lovelace",
  username: "ada",
  email: "ada@example.com",
  bio: "Analytical engines",
  version: 4,
};

// `withFallback` short-circuits to mock data when VITE_API_BASE_URL is empty,
// which would make every assertion below vacuous. Point it at something.
vi.mock("@/api", async () => {
  const actual = await vi.importActual<typeof import("@/api")>("@/api");
  return {
    ...actual,
    isBackendConfigured: () => true,
    usersApi: {
      ...actual.usersApi,
      me: vi.fn(),
      updateMe: vi.fn(),
      updatePrivacySettings: vi.fn(),
      getPrivacySettings: vi.fn(),
    },
  };
});

import { usersApi } from "@/api";
import { usersService } from "@/services";

describe("usersService.getMe", () => {
  beforeEach(() => {
    vi.mocked(usersApi.me).mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("exists, and reads the caller's own profile", async () => {
    vi.mocked(usersApi.me).mockResolvedValue(PROFILE);

    await expect(usersService.getMe()).resolves.toEqual(PROFILE);
    expect(usersApi.me).toHaveBeenCalledTimes(1);
  });

  it("answers null when the profile cannot be read, not an invented user", async () => {
    // A fabricated profile here would be rendered into the form fields as the
    // user's own data, and then written back over the real row on the next
    // save. `null` is the only shape the page can tell apart from an answer.
    vi.mocked(usersApi.me).mockRejectedValue(new Error("network"));
    vi.spyOn(console, "warn").mockImplementation(() => {});

    await expect(usersService.getMe()).resolves.toBeNull();
  });
});

describe("usersService.updateMe", () => {
  beforeEach(() => {
    vi.mocked(usersApi.updateMe).mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("passes the body straight through, version included", async () => {
    vi.mocked(usersApi.updateMe).mockResolvedValue({ ...PROFILE, version: 5 });

    const result = await usersService.updateMe({ bio: "new", version: 4 });

    expect(usersApi.updateMe).toHaveBeenCalledWith({ bio: "new", version: 4 });
    expect(result).toEqual({ ...PROFILE, version: 5 });
  });

  it("rejects when the save fails instead of answering with an empty object", async () => {
    const failure = new Error("500");
    vi.mocked(usersApi.updateMe).mockRejectedValue(failure);

    await expect(usersService.updateMe({ bio: "new" })).rejects.toBe(failure);
  });

  it("lets a 409 reach the caller so the conflict is not reported as a save", async () => {
    // The whole point of sending `version`. Swallowing this was the bug.
    const conflict = Object.assign(new Error("Conflict"), { status: 409 });
    vi.mocked(usersApi.updateMe).mockRejectedValue(conflict);

    await expect(usersService.updateMe({ version: 1 })).rejects.toMatchObject({ status: 409 });
  });
});
