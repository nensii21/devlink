const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export interface ImageUploadResponse {
  url: string;
  thumbnail_url?: string;
  hash?: string;
  reused?: boolean;
}

export type ProgressCallback = (percent: number) => void;

/**
 * Uploads an image Blob/File with upload progress tracking callback.
 */
export async function uploadImage(
  fileOrBlob: File | Blob,
  fileName: string = "image.webp",
  onProgress?: ProgressCallback,
): Promise<ImageUploadResponse> {
  const formData = new FormData();
  const file =
    fileOrBlob instanceof File
      ? fileOrBlob
      : new File([fileOrBlob], fileName, { type: fileOrBlob.type || "image/webp" });

  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/media/upload`, true);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          onProgress(percentComplete);
        } else {
          onProgress(50);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          if (onProgress) onProgress(100);
          resolve(data);
        } catch {
          // If response is not JSON (mock server scenario), fallback
          const objectUrl = URL.createObjectURL(file);
          if (onProgress) onProgress(100);
          resolve({ url: objectUrl, thumbnail_url: objectUrl });
        }
      } else {
        // Fallback for demo / offline environment without backend connection
        const objectUrl = URL.createObjectURL(file);
        if (onProgress) onProgress(100);
        resolve({ url: objectUrl, thumbnail_url: objectUrl });
      }
    };

    xhr.onerror = () => {
      // Fallback for offline / client demo mode
      const objectUrl = URL.createObjectURL(file);
      if (onProgress) onProgress(100);
      resolve({ url: objectUrl, thumbnail_url: objectUrl });
    };

    xhr.send(formData);
  });
}
