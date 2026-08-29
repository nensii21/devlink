import { createFileRoute } from "@tanstack/react-router";
import { RecruiterDashboard } from "@/components/recruiter/RecruiterDashboard";

export const Route = createFileRoute("/_app/recruiter")({
  component: RecruiterDashboard,
});
