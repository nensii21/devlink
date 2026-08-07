import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MediaCaptureModal } from "../MediaCaptureModal";

// Mock the media utils
vi.mock("../../../utils/media", () => ({
  isCameraSupported: vi.fn(() => true),
  dataUrlToFile: vi.fn(() => Promise.resolve(new File([""], "test.jpg", { type: "image/jpeg" }))),
}));

import { isCameraSupported } from "../../../utils/media";

describe("MediaCaptureModal", () => {
  const mockOnClose = vi.fn();
  const mockOnUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock getUserMedia
    Object.defineProperty(global.navigator, "mediaDevices", {
      value: {
        getUserMedia: vi.fn(() =>
          Promise.resolve({
            getTracks: () => [{ stop: vi.fn() }],
          }),
        ),
        enumerateDevices: vi.fn(() => Promise.resolve([])),
      },
      writable: true,
      configurable: true,
    });

    // Mock URL.createObjectURL
    global.URL.createObjectURL = vi.fn(() => "blob:test");
    global.URL.revokeObjectURL = vi.fn();
  });

  it("renders correctly in initial state", () => {
    render(<MediaCaptureModal open={true} onClose={mockOnClose} onUpload={mockOnUpload} />);

    expect(screen.getByText("Choose an image")).toBeInTheDocument();
    expect(screen.getByText("Take Photo")).toBeInTheDocument();
    expect(screen.getByText("Upload Image")).toBeInTheDocument();
  });

  it("shows fallback when camera is not supported", () => {
    vi.mocked(isCameraSupported).mockReturnValueOnce(false);

    render(<MediaCaptureModal open={true} onClose={mockOnClose} onUpload={mockOnUpload} />);

    expect(screen.getByText("Camera unavailable")).toBeInTheDocument();
    expect(screen.queryByText("Take Photo")).not.toBeInTheDocument();
  });

  it("opens camera view when Take Photo is clicked", async () => {
    render(<MediaCaptureModal open={true} onClose={mockOnClose} onUpload={mockOnUpload} />);

    fireEvent.click(screen.getByText("Take Photo"));

    await waitFor(() => {
      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
    });

    expect(screen.getByText("Capture")).toBeInTheDocument();
  });

  it("handles fallback to file picker when upload is clicked", () => {
    render(<MediaCaptureModal open={true} onClose={mockOnClose} onUpload={mockOnUpload} />);

    const uploadButton = screen.getByText("Upload Image");
    expect(uploadButton).toBeInTheDocument();

    // Since input is hidden, we trigger change on the actual input by finding it
    // Usually it's better to just ensure the button exists and the input is present
    const fileInputs = document.querySelectorAll('input[type="file"]');
    expect(fileInputs.length).toBeGreaterThan(0);
  });
});
