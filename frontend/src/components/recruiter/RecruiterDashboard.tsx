import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { recruiterApi } from "@/api/modules/recruiter";
import { projectsApi } from "@/api";
import { Card } from "@/components/shared/primitives";
import { toast } from "sonner";
import { Calendar, MessageSquare, Check, Search, Clock, Link as LinkIcon, User } from "lucide-react";

export function RecruiterDashboard() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const queryClient = useQueryClient();

  const { data: projects } = useQuery({
    queryKey: ["my-projects"],
    queryFn: () => projectsApi.listMyProjects(),
  });

  const { data: applications, isLoading } = useQuery({
    queryKey: ["project-applications", selectedProjectId],
    queryFn: () => recruiterApi.getProjectApplications(selectedProjectId!),
    enabled: !!selectedProjectId,
  });

  const shortlistMutation = useMutation({
    mutationFn: ({ id, shortlisted }: { id: string; shortlisted: boolean }) =>
      recruiterApi.shortlistApplication(id, shortlisted),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-applications", selectedProjectId] });
      toast.success("Application status updated");
    },
  });

  const [notesModalOpen, setNotesModalOpen] = useState(false);
  const [currentAppId, setCurrentAppId] = useState<string | null>(null);
  const [notesContent, setNotesContent] = useState("");

  const notesMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) => recruiterApi.addNotes(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-applications", selectedProjectId] });
      toast.success("Notes saved");
      setNotesModalOpen(false);
    },
  });

  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [interviewDate, setInterviewDate] = useState("");
  const [interviewLink, setInterviewLink] = useState("");

  const interviewMutation = useMutation({
    mutationFn: ({ id, date, link }: { id: string; date: string; link: string }) =>
      recruiterApi.scheduleInterview(id, { interview_scheduled_at: new Date(date).toISOString(), interview_link: link }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-applications", selectedProjectId] });
      toast.success("Interview scheduled");
      setInterviewModalOpen(false);
    },
  });

  const filteredApps = applications?.filter(app => 
    !searchQuery || app.message?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 max-w-6xl space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Recruiter Dashboard</h1>
          <p className="text-muted-foreground">Manage applications and candidates for your projects.</p>
        </div>
        
        <div className="flex w-full md:w-auto gap-3">
          <select 
            className="border border-border bg-surface rounded-md px-3 py-2 text-sm"
            value={selectedProjectId || ""}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            <option value="" disabled>Select a project...</option>
            {projects?.map((p: any) => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              className="pl-8 border border-border bg-surface rounded-md px-3 py-2 text-sm w-full md:w-64"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {!selectedProjectId ? (
        <Card className="p-12 text-center text-muted-foreground">
          <User className="mx-auto h-12 w-12 opacity-20 mb-4" />
          <p>Select a project to view applications.</p>
        </Card>
      ) : isLoading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <Card key={i} className="h-24 animate-pulse bg-muted" />)}
        </div>
      ) : filteredApps?.length === 0 ? (
        <Card className="p-12 text-center text-muted-foreground">
          <p>No applications found for this project.</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredApps?.map(app => (
            <Card key={app.id} className="p-4 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Applicant #{app.applicant_id.substring(0,8)}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold
                    ${app.status === 'accepted' ? 'bg-green-500/10 text-green-500' : 
                      app.status === 'rejected' ? 'bg-red-500/10 text-red-500' : 
                      app.status === 'interviewing' ? 'bg-blue-500/10 text-blue-500' : 
                      app.shortlisted ? 'bg-amber-500/10 text-amber-500' : 
                      'bg-muted text-muted-foreground'}`}>
                    {app.status === 'pending' && app.shortlisted ? 'SHORTLISTED' : app.status}
                  </span>
                </div>
                <p className="text-sm text-foreground line-clamp-2">{app.message || "No message provided."}</p>
                <div className="flex items-center gap-3 text-xs text-muted-foreground mt-2">
                  {app.portfolio_url && <a href={app.portfolio_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-primary"><LinkIcon size={12}/> Portfolio</a>}
                  {app.github_url && <a href={app.github_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-primary"><LinkIcon size={12}/> GitHub</a>}
                  {app.resume_url && <a href={app.resume_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-primary"><LinkIcon size={12}/> Resume</a>}
                </div>
                {app.interview_scheduled_at && (
                  <div className="text-xs text-blue-500 mt-2 flex items-center gap-1">
                    <Clock size={12} /> Interview: {new Date(app.interview_scheduled_at).toLocaleString()}
                    {app.interview_link && <a href={app.interview_link} target="_blank" rel="noreferrer" className="underline ml-1">Join</a>}
                  </div>
                )}
                {app.review_notes && (
                  <div className="text-xs bg-muted/50 p-2 rounded-md mt-2 italic text-muted-foreground">
                    Note: {app.review_notes}
                  </div>
                )}
              </div>
              
              <div className="flex flex-wrap gap-2 md:flex-col md:w-32 shrink-0">
                <button 
                  onClick={() => shortlistMutation.mutate({ id: app.id, shortlisted: !app.shortlisted })}
                  className={`text-xs px-3 py-1.5 rounded-md font-medium border flex items-center justify-center gap-1 w-full
                    ${app.shortlisted ? 'bg-amber-500/10 border-amber-500/30 text-amber-600' : 'bg-surface border-border hover:bg-muted text-foreground'}`}
                >
                  <Check size={14}/> {app.shortlisted ? "Shortlisted" : "Shortlist"}
                </button>
                <button 
                  onClick={() => { setCurrentAppId(app.id); setInterviewModalOpen(true); }}
                  className="text-xs px-3 py-1.5 rounded-md font-medium border border-border bg-surface hover:bg-muted text-foreground flex items-center justify-center gap-1 w-full"
                >
                  <Calendar size={14}/> Schedule
                </button>
                <button 
                  onClick={() => { setCurrentAppId(app.id); setNotesContent(app.review_notes || ""); setNotesModalOpen(true); }}
                  className="text-xs px-3 py-1.5 rounded-md font-medium border border-border bg-surface hover:bg-muted text-foreground flex items-center justify-center gap-1 w-full"
                >
                  <MessageSquare size={14}/> Notes
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Notes Modal */}
      {notesModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <Card className="w-full max-w-md p-6">
            <h2 className="text-lg font-semibold mb-4">Internal Notes</h2>
            <textarea 
              className="w-full border border-border bg-surface rounded-md p-3 text-sm min-h-[100px]"
              value={notesContent}
              onChange={e => setNotesContent(e.target.value)}
              placeholder="Add your thoughts about this candidate..."
            />
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setNotesModalOpen(false)} className="px-4 py-2 text-sm rounded-md hover:bg-muted">Cancel</button>
              <button onClick={() => notesMutation.mutate({ id: currentAppId!, notes: notesContent })} className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground font-semibold">Save Notes</button>
            </div>
          </Card>
        </div>
      )}

      {/* Interview Modal */}
      {interviewModalOpen && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <Card className="w-full max-w-md p-6">
            <h2 className="text-lg font-semibold mb-4">Schedule Interview</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1 block">Date & Time</label>
                <input 
                  type="datetime-local" 
                  className="w-full border border-border bg-surface rounded-md px-3 py-2 text-sm"
                  value={interviewDate}
                  onChange={e => setInterviewDate(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Meeting Link (optional)</label>
                <input 
                  type="url" 
                  placeholder="https://meet.google.com/..."
                  className="w-full border border-border bg-surface rounded-md px-3 py-2 text-sm"
                  value={interviewLink}
                  onChange={e => setInterviewLink(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setInterviewModalOpen(false)} className="px-4 py-2 text-sm rounded-md hover:bg-muted">Cancel</button>
              <button onClick={() => interviewMutation.mutate({ id: currentAppId!, date: interviewDate, link: interviewLink })} disabled={!interviewDate} className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground font-semibold disabled:opacity-50">Schedule</button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
