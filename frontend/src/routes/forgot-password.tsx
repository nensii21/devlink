import { createFileRoute, Link } from "@tanstack/react-router";
import { APP_LOGO } from "@/lib/logo";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";
import { BackButton } from "@/components/shared/BackButton";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({
    meta: [
      { title: "Reset password — DevLink" },
      { name: "description", content: "Recover access to your DevLink account." },
    ],
  }),
  component: ForgotPassword,
});

function ForgotPassword() {
  const [sent, setSent] = useState(false);
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-background px-4">
      <Link to="/" className="mb-6 flex items-center gap-2.5">
        <img src={APP_LOGO} alt="DevLink" className="h-12 w-12 rounded-full" />
        <span className="text-[36px] font-bold tracking-tight text-foreground">DevLink</span>
      </Link>

      <div className="w-full max-w-[440px] rounded-md border border-border bg-surface px-8 py-6">
        <h1 className="text-[18px] font-bold text-foreground">Reset your password</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">
          Enter your email and we'll send you a reset link.
        </p>
        {sent ? (
          <div className="mt-5 rounded-md border border-success/30 bg-success/10 p-4 text-[13px] text-success">
            Check your inbox — a reset link is on its way.
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setSent(true);
              toast.success("Reset link sent");
            }}
            className="mt-5"
          >
            <label className="mb-1 block text-[13px] font-semibold text-foreground">Email</label>
            <input
              type="email"
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
            <button
              type="submit"
              className="mt-4 w-full rounded-md bg-primary py-[9px] text-[14px] font-semibold text-primary-foreground hover:opacity-90 active:scale-[0.98]"
            >
              Send reset link
            </button>
          </form>
        )}
        <BackButton to="/auth" label="Back to sign in" />
      </div>
    </div>
  );
}
