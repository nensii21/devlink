import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProjectMediaUploader } from "../ProjectMediaUploader";

describe("ProjectMediaUploader Component", () => {
  const mockScreenshots = [
    {
      id: "screen-1",
      url: "https://example.com/screenshot1.png",
      type: "image" as const,
      title: "First Screenshot",
      caption: "Initial caption",
      order: 0,
    },
    {
      id: "screen-2",
      url: "https://example.com/screenshot2.png",
      type: "image" as const,
      title: "Second Screenshot",
      caption: "Second caption",
      order: 1,
    },
  ];

  it("does not render when isOpen is false", () => {
    render(<ProjectMediaUploader isOpen={false} onClose={vi.fn()} onSave={vi.fn()} />);
    expect(screen.queryByTestId("project-media-uploader-modal")).not.toBeInTheDocument();
  });

  it("renders modal when isOpen is true with dropzone and inputs", () => {
    render(
      <ProjectMediaUploader
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
        initialCoverImage="https://example.com/cover.png"
        initialScreenshots={mockScreenshots}
        initialVideoDemoUrl="https://youtube.com/watch?v=123"
      />,
    );

    expect(screen.getByTestId("project-media-uploader-modal")).toBeInTheDocument();
    expect(screen.getByTestId("dropzone-area")).toBeInTheDocument();
    expect(screen.getByTestId("video-demo-input")).toHaveValue("https://youtube.com/watch?v=123");
    expect(screen.getByTestId("screenshot-item-0")).toBeInTheDocument();
    expect(screen.getByTestId("screenshot-item-1")).toBeInTheDocument();
  });

  it("allows setting cover image and reordering items", () => {
    const handleSave = vi.fn();
    render(
      <ProjectMediaUploader
        isOpen={true}
        onClose={vi.fn()}
        onSave={handleSave}
        initialScreenshots={mockScreenshots}
      />,
    );

    const setCoverBtn = screen.getByTestId("set-cover-btn-1");
    fireEvent.click(setCoverBtn);

    const moveUpBtn = screen.getByTestId("move-up-btn-1");
    fireEvent.click(moveUpBtn);

    const saveBtn = screen.getByTestId("save-media-btn");
    fireEvent.click(saveBtn);

    expect(handleSave).toHaveBeenCalledWith(
      expect.objectContaining({
        coverImage: "https://example.com/screenshot2.png",
      }),
    );
  });

  it("allows deleting screenshots and editing captions", () => {
    const handleSave = vi.fn();
    render(
      <ProjectMediaUploader
        isOpen={true}
        onClose={vi.fn()}
        onSave={handleSave}
        initialScreenshots={mockScreenshots}
      />,
    );

    const captionInput = screen.getByTestId("caption-input-0");
    fireEvent.change(captionInput, { target: { value: "Updated Custom Caption" } });

    const deleteBtn = screen.getByTestId("delete-screenshot-btn-1");
    fireEvent.click(deleteBtn);

    expect(screen.queryByTestId("screenshot-item-1")).not.toBeInTheDocument();

    const saveBtn = screen.getByTestId("save-media-btn");
    fireEvent.click(saveBtn);

    expect(handleSave).toHaveBeenCalledWith(
      expect.objectContaining({
        screenshots: expect.arrayContaining([
          expect.objectContaining({
            caption: "Updated Custom Caption",
          }),
        ]),
      }),
    );
  });
});
