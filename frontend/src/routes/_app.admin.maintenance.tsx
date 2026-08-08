import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import api from "@/lib/api";

export const Route = createFileRoute("/_app/admin/maintenance")({
  component: AdminMaintenance,
});

interface MaintenanceWindow {
  id: string;
  start_time: string;
  end_time: string;
  message: string;
  is_active: boolean;
}

function AdminMaintenance() {
  const [windows, setWindows] = useState<MaintenanceWindow[]>([]);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [message, setMessage] = useState("The system is undergoing scheduled maintenance.");
  const [isActive, setIsActive] = useState(true);
  const [loading, setLoading] = useState(false);

  const fetchWindows = async () => {
    try {
      setWindows(await api.get<MaintenanceWindow[]>("/api/maintenance"));
    } catch (error) {
      console.error("Failed to fetch maintenance windows", error);
    }
  };

  useEffect(() => {
    void fetchWindows();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        message,
        is_active: isActive,
      };
      await api.post("/api/maintenance", payload);
      alert("Maintenance window scheduled");
      void fetchWindows();
    } catch (error) {
      alert("Failed to schedule maintenance");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this maintenance window?")) return;
    try {
      await api.delete(`/api/maintenance/${id}`);
      void fetchWindows();
    } catch (error) {
      console.error("Failed to delete window", error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Maintenance Mode Configuration</h1>

      <div className="bg-white p-6 rounded shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">Schedule New Window</h2>
        <form onSubmit={handleCreate} className="flex flex-col gap-4 max-w-md">
          <div>
            <label className="block mb-1">Start Time</label>
            <input
              type="datetime-local"
              className="border p-2 w-full rounded"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
            />
          </div>
          <div>
            <label className="block mb-1">End Time</label>
            <input
              type="datetime-local"
              className="border p-2 w-full rounded"
              required
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            />
          </div>
          <div>
            <label className="block mb-1">Message</label>
            <textarea
              className="border p-2 w-full rounded"
              rows={3}
              required
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              Is Active
            </label>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-fit"
          >
            {loading ? "Scheduling..." : "Schedule Maintenance"}
          </button>
        </form>
      </div>

      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-semibold mb-4">Scheduled Windows</h2>
        {windows.length === 0 ? (
          <p>No maintenance windows scheduled.</p>
        ) : (
          <table className="min-w-full text-left">
            <thead>
              <tr className="border-b">
                <th className="p-2">Start Time</th>
                <th className="p-2">End Time</th>
                <th className="p-2">Message</th>
                <th className="p-2">Status</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {windows.map((w) => (
                <tr key={w.id} className="border-b">
                  <td className="p-2">{new Date(w.start_time).toLocaleString()}</td>
                  <td className="p-2">{new Date(w.end_time).toLocaleString()}</td>
                  <td className="p-2 truncate max-w-xs">{w.message}</td>
                  <td className="p-2">
                    {w.is_active ? (
                      <span className="text-green-600">Active</span>
                    ) : (
                      <span className="text-gray-500">Inactive</span>
                    )}
                  </td>
                  <td className="p-2">
                    <button
                      onClick={() => handleDelete(w.id)}
                      className="text-red-500 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
