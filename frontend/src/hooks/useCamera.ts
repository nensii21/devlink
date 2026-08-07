import { useState, useCallback, useRef, useEffect } from "react";
import { isCameraSupported } from "../utils/media";

export type CameraState =
  | "idle"
  | "requesting_permission"
  | "ready"
  | "capturing"
  | "preview"
  | "permission_denied"
  | "unavailable"
  | "error";

export type FacingMode = "user" | "environment";

export const useCamera = () => {
  const [cameraState, setCameraState] = useState<CameraState>("idle");
  const [facingMode, setFacingMode] = useState<FacingMode>("user");
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const videoRef = useRef<HTMLVideoElement>(null);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  const startCamera = useCallback(
    async (mode: FacingMode = facingMode) => {
      if (!isCameraSupported()) {
        setCameraState("unavailable");
        return;
      }

      setCameraState("requesting_permission");
      setErrorMsg("");

      try {
        stopCamera();
        const newStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: mode },
          audio: false,
        });

        setStream(newStream);
        setFacingMode(mode);
        setCameraState("ready");

        if (videoRef.current) {
          videoRef.current.srcObject = newStream;
          const playPromise = videoRef.current.play();
          if (playPromise !== undefined) {
            playPromise.catch((e) => console.error("Error playing video:", e));
          }
        }
      } catch (err: unknown) {
        const error = err as Error;
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
          setCameraState("permission_denied");
        } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
          setCameraState("unavailable");
        } else {
          setCameraState("error");
          setErrorMsg(error.message || "An unknown error occurred while accessing the camera.");
        }
      }
    },
    [facingMode, stopCamera],
  );

  const switchCamera = useCallback(() => {
    const newMode = facingMode === "user" ? "environment" : "user";
    startCamera(newMode);
  }, [facingMode, startCamera]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  return {
    cameraState,
    setCameraState,
    facingMode,
    stream,
    videoRef,
    errorMsg,
    startCamera,
    stopCamera,
    switchCamera,
  };
};
