const stats = [
  {
    title: "Active Projects",
    value: "4",
    change: "+1 this week",
  },
  {
    title: "Applications",
    value: "12",
    change: "3 pending review",
  },
  {
    title: "Messages",
    value: "8",
    change: "3 unread",
  },
  {
    title: "Profile Views",
    value: "94",
    change: "+18 this week",
  },
];

export default function StatsCards() {
  return (
    <section className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map((item) => (
        <div
          key={item.title}
          className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {item.title}
          </p>

          <h2 className="mt-5 text-5xl font-bold text-slate-900">
            {item.value}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            {item.change}
          </p>
        </div>
      ))}
    </section>
  );
}