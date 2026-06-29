import {DashboardLayout} from "../components/layout/DashboardLayout";

export default function Applications() {
  return (
    <DashboardLayout>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">

        <h1 className="text-4xl font-bold text-slate-900">
          Applications
        </h1>

        <p className="mt-3 text-slate-500">
          Review applications from builders.
        </p>

      </div>
    </DashboardLayout>
  );
}