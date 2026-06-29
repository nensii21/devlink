import {DashboardLayout} from "../components/layout/DashboardLayout";

export default function Discover() {
  return (
    <DashboardLayout>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">

        <h1 className="text-4xl font-bold text-slate-900">
          Discover Builders
        </h1>

        <p className="mt-3 text-slate-500">
          Find talented developers, designers and founders.
        </p>

      </div>
    </DashboardLayout>
  );
}