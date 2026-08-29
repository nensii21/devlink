import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ReusableMediaUploader } from "../ReusableMediaUploader";

describe("ReusableMediaUploader Component (#955)", () => {
  it("renders upload dropzone with default preset labels and triggers", () => {
    render(<ReusableMediaUploader />);

    expect(screen.getByText("Drag & drop your file here")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /browse file/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /take photo/i })).toBeInTheDocument();
  });

  it("renders custom preset configurations (avatar, banner, post, organization, project)", () => {
    const { rerender } = render(<ReusableMediaUploader preset="avatar" />);
    expect(screen.getByText("Upload Avatar")).toBeInTheDocument();

    rerender(<ReusableMediaUploader preset="banner" />);
    expect(screen.getByText("Upload Cover Banner")).toBeInTheDocument();

    rerender(<ReusableMediaUploader preset="post" />);
    expect(screen.getByText("Attach Post Image/Video")).toBeInTheDocument();

    rerender(<ReusableMediaUploader preset="organization" />);
    expect(screen.getByText("Org Logo")).toBeInTheDocument();

    rerender(<ReusableMediaUploader preset="project" />);
    expect(screen.getByText("Project Screenshot / Media")).toBeInTheDocument();
  });

  it("validates file size limit and displays error message with retry button", async () => {
    render(<ReusableMediaUploader maxSizeMB={2} />);

    const input = document.querySelector("input[type='file']") as HTMLInputElement;

    // Create a 3MB file
    const largeFile = new File(["a".repeat(3 * 1024 * 1024)], "large.png", {
      type: "image/png",
    });

    fireEvent.change(input, { target: { files: [largeFile] } });

    expect(
      screen.getByText(/file size exceeds the 2mb limit/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("handles valid file upload and displays image preview with remove action", async () => {
    window.URL.createObjectURL = vi.fn(() => "blob:http://localhost/test-preview.jpg");
    const handleChange = vi.fn();
    render(<ReusableMediaUploader onChange={handleChange} />);

    const input = document.querySelector("input[type='file']") as HTMLInputElement;
    const validFile = new File(["valid-image-content"], "test.jpg", {
      type: "image/jpeg",
    });

    fireEvent.change(input, { target: { files: [validFile] } });

    await waitFor(() => {
      expect(handleChange).toHaveBeenCalled();
    });

    await waitFor(
      () => {
        expect(screen.getByRole("button", { name: /remove/i })).toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    // Click remove button
    const removeBtn = screen.getByRole("button", { name: /remove/i });
    fireEvent.click(removeBtn);

    expect(screen.queryByAltText("Media preview")).not.toBeInTheDocument();
    expect(handleChange).toHaveBeenCalledWith(null, null);
  });

  it("handles drag over, drag leave, and drop events", () => {
    render(<ReusableMediaUploader />);

    const dropzone = screen.getByText("Drag & drop your file here").closest("div")!;

    fireEvent.dragOver(dropzone);
    fireEvent.dragLeave(dropzone);

    const validFile = new File(["drag-file"], "drag.png", { type: "image/png" });
    fireEvent.drop(dropzone, {
      dataTransfer: { files: [validFile] },
    });
  });

  it("opens camera capture modal when Take Photo is clicked", () => {
    render(<ReusableMediaUploader enableCamera={true} />);

    const cameraBtn = screen.getByRole("button", { name: /take photo/i });
    fireEvent.click(cameraBtn);

    expect(screen.getByText(/capture image/i)).toBeInTheDocument();
  });
});
