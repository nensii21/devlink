export type PollData = {
  question: string;
  options: string[];
};

export type ArticleData = {
  id?: string;
  title: string;
  content: string;
};

export type Attachment =
  | { type: "image"; file: File; previewUrl: string }
  | { type: "video"; file: File; previewUrl: string }
  | { type: "gif"; file: File; previewUrl: string }
  | { type: "repository"; id: string }
  | { type: "project"; id: string }
  | { type: "poll"; data: PollData }
  | { type: "article"; data: ArticleData };

export type UploadStatus = "idle" | "uploading" | "uploaded" | "error";

export type UploadState = {
  progress: number;
  status: UploadStatus;
};
