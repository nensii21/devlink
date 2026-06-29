import { FileText, MessageSquare, Eye } from "lucide-react";

const activity = [
  {
    name: "Marcus Rivera",
    action: "applied to your AI Startup Platform",
    time: "2h ago",
    icon: FileText,
    color: "bg-cyan-100 text-cyan-600",
  },
  {
    name: "Elena Volkov",
    action: "sent you a message",
    time: "4h ago",
    icon: MessageSquare,
    color: "bg-emerald-100 text-emerald-600",
  },
  {
    name: "Priya Nair",
    action: "viewed your profile",
    time: "1 day ago",
    icon: Eye,
    color: "bg-slate-100 text-slate-500",
  },
];

export default function RecentActivity() {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white shadow-sm">

      <div className="border-b border-slate-100 p-7">
        <h2 className="text-xl font-semibold text-slate-900">
          Recent Activity
        </h2>
      </div>

      <div>
        {activity.map((item) => {
          const Icon = item.icon;

          return (
            <div
              key={item.name}
              className="flex items-center justify-between border-b border-slate-100 px-7 py-5 last:border-0"
            >
              <div>
                <p className="font-semibold text-slate-900">
                  {item.name}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {item.action}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  {item.time}
                </p>
              </div>

              <div
                className={`flex h-12 w-12 items-center justify-center rounded-2xl ${item.color}`}
              >
                <Icon size={20} />
              </div>
            </div>
          );
        })}
      </div>

    </section>
  );
}