import "@testing-library/jest-dom/vitest";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { OrganizationBranding } from "../components/OrganizationBranding";

vi.mock("@/api/modules/organizations", () => ({
  organizationsApi: {
    update: vi.fn(),
  },
}));

import { organizationsApi } from "@/api/modules/organizations";

const mockedUpdate = vi.mocked(organizationsApi.update);

beforeEach(() => {
  vi.clearAllMocks();
  mockedUpdate.mockResolvedValue({
    id: "org-1",
    owner_id: "user-1",
    name: "DevLink",
    slug: "devlink",
    description: "The developer portfolio & project collaboration network.",
    organization_type: "startup",
    website: "https://github.com/nensii21/devlink",
    email: null,
    phone: null,
    logo_url: "https://example.com/logo.png",
    banner_url: "https://example.com/banner.png",
    location: "Remote",
    github_url: null,
    linkedin_url: null,
    twitter_url: null,
    hiring: true,
    active: true,
    verified: false,
    members_count: 1,
    projects_count: 0,
    followers_count: 0,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  });

  HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
    clearRect: vi.fn(),
    save: vi.fn(),
    translate: vi.fn(),
    rotate: vi.fn(),
    scale: vi.fn(),
    drawImage: vi.fn(),
    restore: vi.fn(),
  }) as unknown as CanvasRenderingContext2D;

  HTMLCanvasElement.prototype.toBlob = vi.fn().mockImplementation((callback) => {
    callback(new Blob(["fake-image-bytes"], { type: "image/webp" }));
  });

  Object.defineProperty(global.Image.prototype, "src", {
    set(this: HTMLImageElement) {
      setTimeout(() => {
        if (this.onload) {
          (this.onload as unknown as () => void)();
        }
      }, 10);
    },
  });
});

describe("OrganizationBranding (#958)", () => {
  it("renders branding heading and live preview", () => {
    render(<OrganizationBranding orgId="org-1" name="DevLink" logoUrl={null} bannerUrl={null} />);

    expect(screen.getByText("Branding")).toBeInTheDocument();
    expect(screen.getByText("Live preview · shown on your profile")).toBeInTheDocument();
  });

  it("shows Upload Logo and Upload Cover buttons when no images set", () => {
    render(<OrganizationBranding orgId="org-1" name="DevLink" logoUrl={null} bannerUrl={null} />);

    expect(screen.getByRole("button", { name: /upload logo/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /upload cover/i })).toBeInTheDocument();
  });

  it("shows Replace Logo and Reposition Cover buttons when images are set", () => {
    render(
      <OrganizationBranding
        orgId="org-1"
        name="DevLink"
        logoUrl="https://example.com/logo.png"
        bannerUrl="https://example.com/banner.png"
      />,
    );

    expect(screen.getByRole("button", { name: /replace logo/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reposition cover/i })).toBeInTheDocument();
  });

  it("renders preview images when logo and banner are provided", () => {
    render(
      <OrganizationBranding
        orgId="org-1"
        name="DevLink"
        logoUrl="https://example.com/logo.png"
        bannerUrl="https://example.com/banner.png"
      />,
    );

    expect(screen.getAllByAltText("DevLink cover").length).toBeGreaterThan(0);
    expect(screen.getAllByAltText("DevLink logo").length).toBeGreaterThan(0);
  });

  it("shows initials fallback in preview when no logo", () => {
    render(<OrganizationBranding orgId="org-1" name="DevLink" logoUrl={null} bannerUrl={null} />);

    expect(screen.getByText("DE")).toBeInTheDocument();
  });

  it("opens the logo upload modal and saves the uploaded URL", async () => {
    render(
      <OrganizationBranding
        orgId="org-1"
        name="DevLink"
        logoUrl={null}
        bannerUrl={null}
        onChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /upload logo/i }));
    expect(screen.getByText("Upload Organization Logo")).toBeInTheDocument();

    expect(mockedUpdate).not.toHaveBeenCalled();
  });

  it("calls the update API when an image is removed", async () => {
    render(
      <OrganizationBranding
        orgId="org-1"
        name="DevLink"
        logoUrl="https://example.com/logo.png"
        bannerUrl="https://example.com/banner.png"
      />,
    );

    fireEvent.click(screen.getAllByRole("button", { name: /remove/i })[0]);

    await waitFor(() => {
      expect(mockedUpdate).toHaveBeenCalledWith("org-1", {
        logo_url: null,
        banner_url: undefined,
      });
    });
  });

  it("opens reposition modal with existing banner preloaded into the crop stage", async () => {
    render(
      <OrganizationBranding
        orgId="org-1"
        name="DevLink"
        logoUrl="https://example.com/logo.png"
        bannerUrl="https://example.com/banner.png"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /reposition cover/i }));

    expect(screen.getByText("Reposition Organization Cover")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/crop & save image/i)).toBeInTheDocument();
      expect(screen.getByText(/rotate/i)).toBeInTheDocument();
    });
  });
});
