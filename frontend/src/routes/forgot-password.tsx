import { createFileRoute, Link } from "@tanstack/react-router";
import { APP_LOGO } from "@/lib/logo";
import { useState, useCallback } from "react";
import { toast } from "sonner";
import { BackButton } from "@/components/shared/BackButton";
import { LoadingButton } from "@/components/shared/LoadingButton";

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
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (submitting) return;
      setSubmitting(true);
      try {
        await new Promise((r) => setTimeout(r, 800));
        setSent(true);
        toast.success("Reset link sent");
      } finally {
        setSubmitting(false);
      }
    },
    [submitting],
  );
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-background px-4">
      <Link to="/" className="mb-3 flex items-center gap-2">
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
          <form onSubmit={handleSubmit} className="mt-5">
            <label className="mb-1 block text-[13px] font-semibold text-foreground">Email</label>
            <input
              type="email"
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
            <LoadingButton
              type="submit"
              loading={submitting}
              loadingText="Sending..."
              className="mt-4 w-full py-[9px] text-[14px]"
            >
              Send reset link
            </LoadingButton>
          </form>
        )}
        <BackButton to="/auth" label="Back to sign in" />
      </div>
    </div>
  );
}
