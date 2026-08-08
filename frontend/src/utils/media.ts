export const isCameraSupported = (): boolean => {
  return (
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function"
  );
};

export const dataUrlToBlob = async (dataUrl: string): Promise<Blob> => {
  const res = await fetch(dataUrl);
  return await res.blob();
};

export const dataUrlToFile = async (
  dataUrl: string,
  filename: string,
  mimeType: string = "image/jpeg",
): Promise<File> => {
  const blob = await dataUrlToBlob(dataUrl);
  return new File([blob], filename, { type: mimeType });
};
