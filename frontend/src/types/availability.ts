export interface TimeSlot {
  start: string;
  end: string;
}

export interface WorkingHours {
  [day: string]: TimeSlot[];
}

export interface UserAvailability {
  id: string;
  user_id: string;
  timezone: string;
  working_hours: WorkingHours;
  meeting_duration: number;
  vacation_mode: boolean;
  vacation_start: string | null;
  vacation_end: string | null;
}

export interface AvailabilityUpdate {
  timezone: string;
  working_hours: WorkingHours;
  meeting_duration: number;
  vacation_mode: boolean;
  vacation_start: string | null;
  vacation_end: string | null;
}

export const DAYS_OF_WEEK = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];
