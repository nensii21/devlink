// Regression cover for #1315, at the page level.
//
// Three faults, all in the profile tab of `/settings`:
//
//   1. `useRef` was called without being imported, so the component threw
//      `ReferenceError` on its first render and the route was an error
//      boundary. Every test in this file would fail on that alone.
//   2. `usersService.getMe` did not exist, so the mount effect threw and the
//      form never populated.
//   3. `usersService.updateMe` swallowed failures and returned `{}`, so a save
//      that did not happen was reported as "Profile saved successfully" and
//      the version token was reset to 1 -- which made the *next* save stale too.

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

const PROFILE = {
  id: "usr_1",
  first_name: "Ada",
  last_name: "Lovelace",
  username: "ada",
  email: "ada@example.com",
  headline: "Analytical Engines",
  location: "London",
  website: "https://example.com",
  bio: "Notes on the engine",
  version: 4,
};

const getMe = vi.fn();
const updateMe = vi.fn();

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: any) => ({ options: opts }),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useRouterState: () => "/settings",
}));

vi.mock("@/services", () => ({
  usersService: {
    getMe: (...args: unknown[]) => getMe(...args),
    updateMe: (...args: unknown[]) => updateMe(...args),
    getPrivacySettings: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock("@/api", () => ({
  authApi: { me: vi.fn().mockResolvedValue({}) },
  exportApi: { exportData: vi.fn().mockResolvedValue({ data: {} }) },
}));

const toastSuccess = vi.fn();
const toastError = vi.fn();
vi.mock("sonner", () => ({
  toast: {
    success: (...args: unknown[]) => toastSuccess(...args),
    error: (...args: unknown[]) => toastError(...args),
  },
}));

import { SettingsPage } from "@/routes/_app.settings";

/** Type into the bio field, which is the simplest way to make the form dirty. */
function editBio(value: string) {
  const bio = screen.getByPlaceholderText(/brief overview about your experience/i);
  fireEvent.change(bio, { target: { value } });
  return bio;
}

function submit() {
  fireEvent.click(screen.getByRole("button", { name: /save changes/i }));
}

describe("Settings profile tab (#1315)", () => {
  beforeEach(() => {
    getMe.mockReset().mockResolvedValue(PROFILE);
    updateMe.mockReset().mockResolvedValue({ ...PROFILE, bio: "edited", version: 5 });
    toastSuccess.mockReset();
    toastError.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders without throwing", () => {
    // The `useRef` regression: this threw `ReferenceError: useRef is not
    // defined` before anything painted.
    expect(() => render(<SettingsPage />)).not.toThrow();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Settings");
  });

  it("loads the profile through usersService.getMe and fills the form", async () => {
    render(<SettingsPage />);

    await waitFor(() => expect(getMe).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.getByDisplayValue("Notes on the engine")).toBeInTheDocument(),
    );
    expect(screen.getByDisplayValue("ada@example.com")).toBeInTheDocument();
  });

  it("says so when the profile cannot be loaded", async () => {
    getMe.mockResolvedValue(null);

    render(<SettingsPage />);

    await waitFor(() =>
      expect(screen.getByText(/could not load your profile/i)).toBeInTheDocument(),
    );
  });

  it("sends the loaded version with the save", async () => {
    render(<SettingsPage />);
    await waitFor(() =>
      expect(screen.getByDisplayValue("Notes on the engine")).toBeInTheDocument(),
    );

    editBio("edited");
    submit();

    await waitFor(() => expect(updateMe).toHaveBeenCalledTimes(1));
    expect(updateMe.mock.calls[0][0]).toMatchObject({ bio: "edited", version: 4 });
  });

  it("reports a failed save as a failure", async () => {
    updateMe.mockRejectedValue(new Error("Network is down"));

    render(<SettingsPage />);
    await waitFor(() =>
      expect(screen.getByDisplayValue("Notes on the engine")).toBeInTheDocument(),
    );

    editBio("edited");
    submit();

    await waitFor(() => expect(screen.getByText("Network is down")).toBeInTheDocument());
    expect(toastSuccess).not.toHaveBeenCalled();
    expect(toastError).toHaveBeenCalled();
  });

  it("routes a 409 to the conflict state rather than reporting a save", async () => {
    updateMe.mockRejectedValue(Object.assign(new Error("Conflict"), { status: 409 }));

    render(<SettingsPage />);
    await waitFor(() =>
      expect(screen.getByDisplayValue("Notes on the engine")).toBeInTheDocument(),
    );

    editBio("edited");
    submit();

    await waitFor(() => expect(screen.getByText(/profile updated elsewhere/i)).toBeInTheDocument());
    expect(toastSuccess).not.toHaveBeenCalled();
  });

  it("keeps the version the server returned after a successful save", async () => {
    // The old code read `version` off a `{}` fallback, so it reset to 1 and
    // every later save was sent with a stale token.
    render(<SettingsPage />);
    await waitFor(() =>
      expect(screen.getByDisplayValue("Notes on the engine")).toBeInTheDocument(),
    );

    editBio("edited");
    submit();
    await waitFor(() => expect(toastSuccess).toHaveBeenCalled());

    editBio("edited twice");
    submit();

    await waitFor(() => expect(updateMe).toHaveBeenCalledTimes(2));
    expect(updateMe.mock.calls[1][0]).toMatchObject({ version: 5 });
  });
});
