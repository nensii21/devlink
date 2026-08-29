import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectMediaGallery } from "../ProjectMediaGallery";

describe("ProjectMediaGallery Component", () => {
  const mockScreenshots = [
    {
      id: "screen-1",
      url: "https://example.com/screenshot1.png",
      type: "image" as const,
      title: "Dashboard Overview",
      caption: "Real-time metrics view",
      order: 0,
    },
    {
      id: "screen-2",
      url: "https://example.com/screenshot2.png",
      type: "image" as const,
      title: "Settings View",
      caption: "Security and preferences",
      order: 1,
    },
  ];

  it("renders empty state when no media is provided", () => {
    const onManage = vi.fn();
    render(<ProjectMediaGallery isOwner onManageMedia={onManage} />);

    expect(screen.getByText("No media uploaded yet")).toBeInTheDocument();
    const manageBtn = screen.getByText("Upload Screenshots & Demo");
    expect(manageBtn).toBeInTheDocument();
    fireEvent.click(manageBtn);
    expect(onManage).toHaveBeenCalledTimes(1);
  });

  it("renders cover image, screenshots, and thumbnails", () => {
    render(
      <ProjectMediaGallery
        coverImage="https://example.com/cover.png"
        screenshots={mockScreenshots}
      />,
    );

    expect(screen.getByTestId("project-media-gallery")).toBeInTheDocument();
    expect(screen.getByText("Project Gallery & Demos")).toBeInTheDocument();
    expect(screen.getByText("3 items")).toBeInTheDocument();
    expect(screen.getByTestId("gallery-thumb-0")).toBeInTheDocument();
    expect(screen.getByTestId("gallery-thumb-1")).toBeInTheDocument();
    expect(screen.getByTestId("gallery-thumb-2")).toBeInTheDocument();
  });

  it("switches active media when thumbnail is clicked", () => {
    render(
      <ProjectMediaGallery
        coverImage="https://example.com/cover.png"
        screenshots={mockScreenshots}
      />,
    );

    const thumb1 = screen.getByTestId("gallery-thumb-1");
    fireEvent.click(thumb1);
    expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();
    expect(screen.getByText("Real-time metrics view")).toBeInTheDocument();
  });

  it("opens fullscreen lightbox modal and navigates", () => {
    render(
      <ProjectMediaGallery
        coverImage="https://example.com/cover.png"
        screenshots={mockScreenshots}
      />,
    );

    const lightboxBtn = screen.getByTestId("open-lightbox-btn");
    fireEvent.click(lightboxBtn);

    expect(screen.getByTestId("lightbox-modal")).toBeInTheDocument();

    const closeBtn = screen.getByTestId("close-lightbox-btn");
    fireEvent.click(closeBtn);
    expect(screen.queryByTestId("lightbox-modal")).not.toBeInTheDocument();
  });

  it("renders video demo player when video demo url is provided", () => {
    render(
      <ProjectMediaGallery
        videoDemoUrl="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        screenshots={mockScreenshots}
      />,
    );

    const videoThumb = screen.getByTestId("gallery-thumb-1");
    fireEvent.click(videoThumb);

    expect(screen.getAllByText("Video Demo").length).toBeGreaterThan(0);
    const iframe = screen.getByTitle("Video Demo");
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute("src")).toContain("youtube.com/embed/dQw4w9WgXcQ");
  });
});
