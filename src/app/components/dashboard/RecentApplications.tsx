export default function RecentApplications() {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">

      <h2 className="mb-6 text-xl font-semibold text-slate-900">
        Recent Applications
      </h2>

      {[1, 2].map((item) => (
        <div
          key={item}
          className="mb-6 rounded-2xl border border-slate-200 p-5 last:mb-0"
        >
          <h3 className="font-semibold text-slate-900">
            Marcus Rivera
          </h3>

          <p className="mt-1 text-sm text-slate-500">
            ML Engineer
          </p>

          <div className="mt-5 flex gap-3">
            <button className="rounded-full bg-cyan-500 px-6 py-2 font-medium text-white transition hover:bg-cyan-600">
              Accept
            </button>

            <button className="rounded-full border border-slate-300 px-6 py-2 font-medium text-slate-600 transition hover:bg-slate-100">
              Decline
            </button>
          </div>
        </div>
      ))}

    </section>
  );
}