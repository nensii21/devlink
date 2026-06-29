import {DashboardLayout} from "../components/layout/DashboardLayout";

export default function Messages() {
  return (
    <DashboardLayout>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">

        <h1 className="text-4xl font-bold text-slate-900">
          Messages
        </h1>

        <p className="mt-3 text-slate-500">
          Stay connected with your collaborators.
        </p>

      </div>
    </DashboardLayout>
  );
}