import "@testing-library/jest-dom/vitest";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ImageCropUploadModal } from "@/components/shared/ImageCropUploadModal";
import { UserAvatar } from "@/components/user-avatar";

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

  // Mock HTMLImageElement image loading in jsdom
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

describe("ImageCropUploadModal (#575)", () => {
  it("renders drag and drop zone when open", () => {
    render(
      <ImageCropUploadModal
        isOpen={true}
        onClose={vi.fn()}
        onUploadSuccess={vi.fn()}
        mode="avatar"
      />,
    );

    expect(screen.getByText(/upload avatar image/i)).toBeInTheDocument();
    expect(screen.getByText(/drag & drop your image here/i)).toBeInTheDocument();
  });

  it("validates file type and displays error for non-image files", async () => {
    render(
      <ImageCropUploadModal
        isOpen={true}
        onClose={vi.fn()}
        onUploadSuccess={vi.fn()}
        mode="avatar"
      />,
    );

    const input = screen.getByTestId("file-input");
    const textFile = new File(["hello text"], "doc.txt", {
      type: "text/plain",
    });

    fireEvent.change(input, { target: { files: [textFile] } });

    expect(await screen.findByText(/please select a valid image file/i)).toBeInTheDocument();
  });

  it("loads valid image file into preview & crop view", async () => {
    vi.spyOn(FileReader.prototype, "readAsDataURL").mockImplementation(function (this: FileReader) {
      Object.defineProperty(this, "result", {
        value: "data:image/png;base64,fakebytes",
      });
      if (this.onload) {
        this.onload({ target: this } as unknown as ProgressEvent<FileReader>);
      }
    });

    render(
      <ImageCropUploadModal
        isOpen={true}
        onClose={vi.fn()}
        onUploadSuccess={vi.fn()}
        mode="avatar"
      />,
    );

    const input = screen.getByTestId("file-input");
    const imageFile = new File(["dummy image content"], "avatar.png", {
      type: "image/png",
    });

    fireEvent.change(input, { target: { files: [imageFile] } });

    await waitFor(() => {
      expect(screen.getByText(/rotate/i)).toBeInTheDocument();
      expect(screen.getByText(/reset/i)).toBeInTheDocument();
      expect(screen.getByText(/crop & save image/i)).toBeInTheDocument();
    });
  });

  it("triggers upload and shows progress indicator bar on click", async () => {
    vi.spyOn(FileReader.prototype, "readAsDataURL").mockImplementation(function (this: FileReader) {
      Object.defineProperty(this, "result", {
        value: "data:image/png;base64,fakebytes",
      });
      if (this.onload) {
        this.onload({ target: this } as unknown as ProgressEvent<FileReader>);
      }
    });

    const handleSuccess = vi.fn();
    render(
      <ImageCropUploadModal
        isOpen={true}
        onClose={vi.fn()}
        onUploadSuccess={handleSuccess}
        mode="avatar"
      />,
    );

    const input = screen.getByTestId("file-input");
    const imageFile = new File(["dummy image content"], "avatar.png", {
      type: "image/png",
    });

    fireEvent.change(input, { target: { files: [imageFile] } });

    const saveBtn = await screen.findByText(/crop & save image/i);
    fireEvent.click(saveBtn);

    expect(await screen.findByText(/uploading image.../i)).toBeInTheDocument();
  });
});

describe("UserAvatar with editable crop uploader", () => {
  it("renders hover camera icon overlay when editable", () => {
    const { container } = render(<UserAvatar name="Ada Lovelace" size="lg" editable />);

    expect(container.querySelector(".lucide-camera")).toBeInTheDocument();
  });

  it("opens ImageCropUploadModal when editable avatar is clicked", () => {
    render(<UserAvatar name="Ada Lovelace" size="lg" editable />);

    const avatarElement = screen.getByText("AL").closest("span");
    expect(avatarElement).toBeInTheDocument();

    if (avatarElement) {
      fireEvent.click(avatarElement);
    }

    expect(screen.getByText(/upload avatar image/i)).toBeInTheDocument();
  });
});
