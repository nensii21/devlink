import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import { ApiError } from "@/api/client";
import { TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/maintenance")({
  component: MaintenancePage,
});

interface MaintenanceWindow {
  message: string;
  end_time: string;
}

/**
 * A 503 from the maintenance middleware carries the window in its body. The
 * shape is not guaranteed by anything the client can see, so it is narrowed
 * rather than asserted.
 */
function maintenanceFromErrorPayload(payload: unknown): MaintenanceWindow | null {
  if (typeof payload !== "object" || payload === null) return null;
  const maintenance = (payload as { maintenance?: unknown }).maintenance;
  if (typeof maintenance !== "object" || maintenance === null) return null;

  const { message, end_time: endTime } = maintenance as Record<string, unknown>;
  if (typeof message !== "string" || typeof endTime !== "string") return null;

  return { message, end_time: endTime };
}

function MaintenancePage() {
  const [maintenance, setMaintenance] = useState<MaintenanceWindow | null>(null);
  const [timeLeft, setTimeLeft] = useState<string>("");

  useEffect(() => {
    const checkMaintenance = async () => {
      try {
        setMaintenance(await api.get<MaintenanceWindow>("/api/maintenance/active"));
      } catch (error) {
        if (!(error instanceof ApiError)) return;

        if (error.status === 404) {
          window.location.href = "/";
          return;
        }

        if (error.status === 503) {
          setMaintenance(maintenanceFromErrorPayload(error.payload));
        }
      }
    };
    void checkMaintenance();
  }, []);

  useEffect(() => {
    if (!maintenance?.end_time) return;

    const interval = setInterval(() => {
      const now = new Date().getTime();
      const end = new Date(maintenance.end_time).getTime();
      const distance = end - now;

      if (distance < 0) {
        clearInterval(interval);
        setTimeLeft("Maintenance should be finishing up soon...");
        return;
      }

      const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);

      setTimeLeft(`${hours}h ${minutes}m ${seconds}s remaining`);
    }, 1000);

    return () => clearInterval(interval);
  }, [maintenance]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="bg-white shadow-lg rounded-lg p-8 max-w-md w-full text-center">
        <TypoHeading as="h1">Under Maintenance</TypoHeading>
        <p className="text-gray-600 mb-6">
          {maintenance?.message ||
            "The system is currently undergoing scheduled maintenance. Please check back later."}
        </p>

        {timeLeft && (
          <div className="bg-blue-50 text-blue-800 p-4 rounded-md">
            <p className="font-semibold text-lg">{timeLeft}</p>
          </div>
        )}
      </div>
    </div>
  );
}
