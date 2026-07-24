import React from "react";
import { formatDistanceToNow } from "date-fns";
import { Activity } from "@/api/modules/activities";
import {
  UserPlus,
  FolderPlus,
  Edit3,
  Archive,
  Flag,
  Send,
  CheckCircle,
  XCircle,
  Mail,
  Github,
  MessageSquare,
  MessageCircle,
  Users,
  Info,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface ActivityItemProps {
  activity: Activity;
}

const getActivityIcon = (type: Activity["activity_type"]) => {
  switch (type) {
    case "user_registered":
      return <UserPlus className="w-4 h-4 text-green-500" />;
    case "profile_updated":
      return <Edit3 className="w-4 h-4 text-blue-500" />;
    case "project_created":
      return <FolderPlus className="w-4 h-4 text-indigo-500" />;
    case "project_updated":
      return <Edit3 className="w-4 h-4 text-blue-400" />;
    case "project_archived":
      return <Archive className="w-4 h-4 text-gray-500" />;
    case "project_milestone":
      return <Flag className="w-4 h-4 text-yellow-500" />;
    case "application_submitted":
      return <Send className="w-4 h-4 text-purple-500" />;
    case "application_accepted":
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case "application_rejected":
      return <XCircle className="w-4 h-4 text-red-500" />;
    case "team_invitation":
      return <Mail className="w-4 h-4 text-blue-500" />;
    case "repository_connected":
      return <Github className="w-4 h-4 text-gray-700" />;
    case "followed_user":
      return <UserPlus className="w-4 h-4 text-pink-500" />;
    case "message_sent":
      return <MessageSquare className="w-4 h-4 text-blue-500" />;
    case "comment_created":
      return <MessageCircle className="w-4 h-4 text-indigo-500" />;
    case "discussion_created":
      return <MessageCircle className="w-4 h-4 text-purple-500" />;
    case "organization_created":
      return <Users className="w-4 h-4 text-orange-500" />;
    default:
      return <Info className="w-4 h-4 text-gray-400" />;
  }
};

export function ActivityItem({ activity }: ActivityItemProps) {
  // Use metadata for extra rendering details if available
  const metadata = (activity.metadata ?? {}) as {
    actor_name?: string;
    actor_avatar?: string;
  };

  const actorName = metadata.actor_name ?? "Someone";
  const actorAvatar = metadata.actor_avatar;

  return (
    <div className="flex gap-4 p-4 rounded-lg bg-white shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="relative shrink-0 mt-1">
        <Avatar className="w-10 h-10 border border-gray-200">
          <AvatarImage src={actorAvatar} alt={actorName} />
          <AvatarFallback>{actorName.slice(0, 2).toUpperCase()}</AvatarFallback>
        </Avatar>
        <div className="absolute -bottom-1 -right-1 p-1 bg-white rounded-full shadow-sm border border-gray-100">
          {getActivityIcon(activity.activity_type)}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-1">
          <p className="text-sm font-medium text-gray-900 truncate">{activity.title}</p>
          <time className="text-xs text-gray-500 whitespace-nowrap">
            {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
          </time>
        </div>
        {activity.description && (
          <p className="text-sm text-gray-600 line-clamp-2">{activity.description}</p>
        )}
      </div>
    </div>
  );
}
