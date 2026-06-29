import {DashboardLayout} from "../components/layout/DashboardLayout";

export default function Settings() {
  return (
    <DashboardLayout>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">

        <h1 className="text-4xl font-bold text-slate-900">
          Settings
        </h1>

        <p className="mt-3 text-slate-500">
          Configure your DevLink account.
        </p>

      </div>
    </DashboardLayout>
  );
}