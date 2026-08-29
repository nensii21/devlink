import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle, Clock, XCircle, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TypoSection, TypoCaption, TypoCard, TypoHeading } from "@/components/shared/Typography";

export const Route = createFileRoute("/_app/admin/notifications")({
  component: AdminNotificationsPage,
});

function AdminNotificationsPage() {
  const queryClient = useQueryClient();

  interface FailedNotification {
    id: string;
    title: string;
    message: string;
    channel: string;
    recipient_id: string;
  }

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["admin-notification-stats"],
    // The API client already resolves to the parsed body. Reading `.data` off
    // it handed React Query `undefined`, so every tile rendered its `|| 0`
    // fallback no matter what the server said.
    queryFn: async () => {
      return api.get<{
        total: number;
        pending: number;
        sent: number;
        failed: number;
      }>("/admin/notifications/stats");
    },
  });

  const { data: failed, isLoading: failedLoading } = useQuery({
    queryKey: ["admin-notification-failed"],
    queryFn: async () => {
      return api.get<FailedNotification[]>("/admin/notifications/failed");
    },
  });

  const retryMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/admin/notifications/${id}/retry`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-notification-stats"] });
      queryClient.invalidateQueries({ queryKey: ["admin-notification-failed"] });
    },
  });

  if (statsLoading || failedLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div>
        <TypoHeading as="h2">Notification Delivery Stats</TypoHeading>
        <TypoCaption as="p">
          Monitor the global delivery metrics for unified notifications.
        </TypoCaption>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Notifications</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Delivery</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Delivered (Sent)</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.sent || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Delivery Failures</CardTitle>
            <XCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.failed || 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <TypoSection>Failed Deliveries Queue</TypoSection>
        {failed?.length === 0 ? (
          <TypoCaption as="p">No failed deliveries to display.</TypoCaption>
        ) : (
          <div className="space-y-4">
            {failed?.map((notification: FailedNotification) => (
              <Card key={notification.id}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <TypoCard>
                      {notification.title}
                      <Badge variant="destructive">Failed</Badge>
                      <Badge variant="outline">{notification.channel}</Badge>
                    </TypoCard>
                    <TypoCaption as="p">{notification.message}</TypoCaption>
                    <TypoCaption as="p">Recipient: {notification.recipient_id}</TypoCaption>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={retryMutation.isPending}
                    onClick={() => retryMutation.mutate(notification.id)}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry Delivery
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
