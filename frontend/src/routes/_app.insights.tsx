/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import { createFileRoute } from '@tanstack/react-router';
import { DeveloperInsightsDashboard } from '../components/dashboard/DeveloperInsightsDashboard';

export const Route = createFileRoute('/_app/insights')({
  component: InsightsPage,
});

function InsightsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <DeveloperInsightsDashboard />
    </div>
  );
}
