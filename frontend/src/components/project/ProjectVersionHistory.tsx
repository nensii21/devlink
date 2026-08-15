import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { TypoSection, TypoCaption } from "@/components/shared/Typography";

interface ProjectVersion {
  id: string;
  project_id: string;
  version_number: number;
  title: string;
  tagline?: string;
  description: string;
  tech_stack?: string;
  requirements?: string;
  stage: string;
  change_summary?: string;
  created_at: string;
}

interface DiffField {
  old: unknown;
  new: unknown;
}

interface CompareResponse {
  v1_version_number: number;
  v2_version_number: string | number;
  diff: Record<string, DiffField>;
}

interface ProjectVersionHistoryProps {
  projectId: string;
  isOwnerOrMaintainer?: boolean;
}

export function ProjectVersionHistory({
  projectId,
  isOwnerOrMaintainer = true,
}: ProjectVersionHistoryProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);

  const { data: versionsData, isLoading } = useQuery({
    queryKey: ["project-versions", projectId],
    queryFn: async () => {
      const res = (await api.get(`/api/projects/${projectId}/versions`)) as any;
      return res?.data || res;
    },
  });

  const compareMutation = useMutation({
    mutationFn: async (v1: number) => {
      const res = (await api.get(
        `/api/projects/${projectId}/versions/compare?v1=${v1}&v2=current`,
      )) as any;
      return res?.data || res;
    },
    onSuccess: (data) => {
      setCompareData(data);
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to load version comparison.",
      });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: async (v1: number) => {
      const res = (await api.post(`/api/projects/${projectId}/versions/${v1}/restore`)) as any;
      return res?.data || res;
    },

    onSuccess: (_, v1) => {
      queryClient.invalidateQueries({ queryKey: ["project-versions", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setCompareData(null);
      setSelectedVersion(null);
      toast({
        title: "Version Restored",
        description: `Project details successfully restored to Version ${v1}.`,
      });
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to restore version snapshot.",
      });
    },
  });

  const handleSelectVersion = (v: number) => {
    setSelectedVersion(v);
    compareMutation.mutate(v);
  };

  if (isLoading) return <div className="p-4 text-muted-foreground">Loading version history...</div>;

  const versions: ProjectVersion[] = versionsData?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <TypoSection>Project Version History</TypoSection>
          <TypoCaption as="p">
            Review previous edits, compare field diffs, and restore prior project snapshots.
          </TypoCaption>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Version List Sidebar */}
        <div className="space-y-3 md:col-span-1">
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-semibold">
                Version Revisions ({versions.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 p-3">
              {versions.map((ver) => (
                <div
                  key={ver.id}
                  onClick={() => handleSelectVersion(ver.version_number)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedVersion === ver.version_number
                      ? "bg-primary/10 border-primary"
                      : "hover:bg-accent/50 border-border"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">v{ver.version_number}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {new Date(ver.created_at).toLocaleDateString()}
                    </Badge>
                  </div>
                  <TypoCaption as="p">{ver.change_summary || ver.title}</TypoCaption>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Compare / View Panel */}
        <div className="md:col-span-2 space-y-4">
          {compareData ? (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-lg">
                    Comparison: v{compareData.v1_version_number} vs Current
                  </CardTitle>
                  <CardDescription>
                    Review changed fields between Version {compareData.v1_version_number} and the
                    active project state.
                  </CardDescription>
                </div>
                {isOwnerOrMaintainer && (
                  <Button
                    size="sm"
                    onClick={() => restoreMutation.mutate(compareData.v1_version_number)}
                    disabled={restoreMutation.isPending}
                  >
                    {restoreMutation.isPending
                      ? "Restoring..."
                      : `Restore v${compareData.v1_version_number}`}
                  </Button>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.keys(compareData.diff).length === 0 ? (
                  <TypoCaption as="p">
                    No differences detected between version {compareData.v1_version_number} and
                    current state.
                  </TypoCaption>
                ) : (
                  Object.entries(compareData.diff).map(([field, { old: oldVal, new: newVal }]) => (
                    <div key={field} className="p-3 border rounded-md space-y-2">
                      <TypoCaption>{field}</TypoCaption>
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div className="p-2 bg-red-500/10 rounded border border-red-500/20">
                          <span className="font-semibold text-red-600 block mb-1">
                            v{compareData.v1_version_number} (Old):
                          </span>
                          <pre className="whitespace-pre-wrap font-sans">
                            {String(oldVal ?? "None")}
                          </pre>
                        </div>
                        <div className="p-2 bg-green-500/10 rounded border border-green-500/20">
                          <span className="font-semibold text-green-600 block mb-1">
                            Current (New):
                          </span>
                          <pre className="whitespace-pre-wrap font-sans">
                            {String(newVal ?? "None")}
                          </pre>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                Select a version from the timeline on the left to view diffs and restore previous
                changes.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
