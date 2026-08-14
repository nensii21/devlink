import "@testing-library/jest-dom/vitest";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { createRef } from "react";
import { ImageCropper, ImageCropperHandle, CROP_PRESETS } from "@/components/shared/ImageCropper";

beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
    clearRect: vi.fn(),
    save: vi.fn(),
    translate: vi.fn(),
    rotate: vi.fn(),
    scale: vi.fn(),
    drawImage: vi.fn(),
    restore: vi.fn(),
    beginPath: vi.fn(),
    arc: vi.fn(),
    clip: vi.fn(),
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

function mockImageSize(width = 800, height = 600) {
  Object.defineProperty(global.Image.prototype, "width", {
    get: () => width,
    configurable: true,
  });
  Object.defineProperty(global.Image.prototype, "height", {
    get: () => height,
    configurable: true,
  });
}

describe("ImageCropper", () => {
  it("exports crop presets for supported use cases", () => {
    expect(CROP_PRESETS).toEqual(
      expect.objectContaining({
        avatar: expect.objectContaining({ shape: "circle", aspectRatio: 1 }),
        "org-logo": expect.objectContaining({ shape: "square", aspectRatio: 1 }),
        banner: expect.objectContaining({ shape: "banner", aspectRatio: 3 }),
        "project-cover": expect.objectContaining({ shape: "banner" }),
      }),
    );
  });

  it("renders the canvas and crop controls", async () => {
    mockImageSize();
    render(<ImageCropper src="data:image/png;base64,fakebytes" />);

    expect(screen.getByTestId("cropper-canvas")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /rotate/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reset/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/zoom/i)).toBeInTheDocument();
  });

  it("hides controls when showControls is false", () => {
    render(<ImageCropper src="data:image/png;base64,fakebytes" showControls={false} />);

    expect(screen.getByTestId("cropper-canvas")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /rotate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reset/i })).not.toBeInTheDocument();
  });

  it("rotates 90 degrees when the rotate button is clicked", async () => {
    mockImageSize();
    render(<ImageCropper src="data:image/png;base64,fakebytes" />);

    const rotateBtn = await screen.findByRole("button", { name: /rotate/i });
    fireEvent.click(rotateBtn);
    fireEvent.click(rotateBtn);
    fireEvent.click(rotateBtn);
    fireEvent.click(rotateBtn);

    expect(rotateBtn).toBeInTheDocument();
  });

  it("reset restores default zoom state", async () => {
    mockImageSize();
    render(<ImageCropper src="data:image/png;base64,fakebytes" />);

    const zoomLabel = screen.getByLabelText(/zoom/i);
    const resetBtn = await screen.findByRole("button", { name: /reset/i });

    act(() => {
      fireEvent.keyDown(document.activeElement ?? document.body, { key: "Tab" });
    });

    fireEvent.click(resetBtn);
    expect(zoomLabel).toBeInTheDocument();
  });

  it("exposes getCropBlob through the ref handle", async () => {
    mockImageSize();
    const ref = createRef<ImageCropperHandle>();
    render(<ImageCropper ref={ref} src="data:image/png;base64,fakebytes" />);

    await new Promise((resolve) => setTimeout(resolve, 30));

    expect(ref.current).toBeTruthy();
    expect(ref.current?.getCropBlob).toBeTypeOf("function");

    const blob = await ref.current?.getCropBlob();
    expect(blob).toBeInstanceOf(Blob);
  });

  it("exposes reset and rotate through the ref handle", async () => {
    mockImageSize();
    const ref = createRef<ImageCropperHandle>();
    render(<ImageCropper ref={ref} src="data:image/png;base64,fakebytes" />);

    await new Promise((resolve) => setTimeout(resolve, 30));

    expect(ref.current?.reset).toBeTypeOf("function");
    expect(ref.current?.rotate).toBeTypeOf("function");
    ref.current?.reset();
    ref.current?.rotate();
  });
});
