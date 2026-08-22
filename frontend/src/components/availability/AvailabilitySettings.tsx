import React, { useEffect, useState } from "react";
import { useMyAvailability, useUpdateAvailability } from "../../hooks/useAvailability";
import { AvailabilityUpdate, DAYS_OF_WEEK } from "../../types/availability";
import { WorkingHours } from "./WorkingHours";
import { TimezoneSelector } from "./TimezoneSelector";
import { MeetingAvailability } from "./MeetingAvailability";
import { VacationMode } from "./VacationMode";
import { LoadingButton } from "../shared/LoadingButton";
import { Card } from "../shared/primitives";
import { Calendar } from "lucide-react";

export const AvailabilitySettings: React.FC = () => {
  const { data: availability, isLoading } = useMyAvailability();
  const updateMutation = useUpdateAvailability();

  const [formData, setFormData] = useState<AvailabilityUpdate>({
    timezone: "UTC",
    working_hours: {},
    meeting_duration: 30,
    vacation_mode: false,
    vacation_start: null,
    vacation_end: null,
  });

  useEffect(() => {
    if (availability) {
      setFormData({
        timezone: availability.timezone,
        working_hours: availability.working_hours || {},
        meeting_duration: availability.meeting_duration,
        vacation_mode: availability.vacation_mode,
        vacation_start: availability.vacation_start,
        vacation_end: availability.vacation_end,
      });
    }
  }, [availability]);

  if (isLoading) {
    return <div className="animate-pulse h-64 bg-surface-100 rounded-xl" />;
  }

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="h-10 w-10 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center">
          <Calendar className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-surface-900">Availability Settings</h2>
          <p className="text-sm text-surface-500">
            Manage when you are available for collaboration.
          </p>
        </div>
      </div>

      <div className="space-y-8">
        <TimezoneSelector
          value={formData.timezone}
          onChange={(timezone) => setFormData((prev) => ({ ...prev, timezone }))}
        />

        <div className="border-t border-surface-200 pt-6">
          <WorkingHours
            value={formData.working_hours}
            onChange={(working_hours) => setFormData((prev) => ({ ...prev, working_hours }))}
          />
        </div>

        <div className="border-t border-surface-200 pt-6">
          <MeetingAvailability
            value={formData.meeting_duration}
            onChange={(meeting_duration) => setFormData((prev) => ({ ...prev, meeting_duration }))}
          />
        </div>

        <div className="border-t border-surface-200 pt-6">
          <VacationMode
            mode={formData.vacation_mode}
            start={formData.vacation_start}
            end={formData.vacation_end}
            onChangeMode={(vacation_mode) => setFormData((prev) => ({ ...prev, vacation_mode }))}
            onChangeStart={(vacation_start) => setFormData((prev) => ({ ...prev, vacation_start }))}
            onChangeEnd={(vacation_end) => setFormData((prev) => ({ ...prev, vacation_end }))}
          />
        </div>

        <div className="border-t border-surface-200 pt-6 flex justify-end">
          <LoadingButton
            onClick={handleSave}
            loading={updateMutation.isPending}
            className="w-full sm:w-auto"
          >
            Save Availability
          </LoadingButton>
        </div>
      </div>
    </Card>
  );
};
