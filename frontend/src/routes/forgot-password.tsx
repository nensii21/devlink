import { createFileRoute, Link } from "@tanstack/react-router";
import { APP_LOGO } from "@/lib/logo";
import { useState, useCallback } from "react";
import { toast } from "sonner";
import { BackButton } from "@/components/shared/BackButton";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { authApi } from "@/api/modules/auth";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

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
  const [email, setEmail] = useState("");

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (submitting || !email) return;
      setSubmitting(true);
      try {
        await authApi.forgotPassword(email);
        setSent(true);
        toast.success("Reset link sent");
      } catch (err: unknown) {
        toast.error((err as Error).message || "Failed to send reset link");
      } finally {
        setSubmitting(false);
      }
    },
    [submitting, email],
  );
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-background px-4">
      <Link to="/" className="mb-3 flex items-center gap-2">
        <img src={APP_LOGO} alt="DevLink" className="h-12 w-12 rounded-full" />
        <span className="text-[36px] font-bold tracking-tight text-foreground">DevLink</span>
      </Link>

      <div className="w-full max-w-[440px] rounded-md border border-border bg-surface px-8 py-6">
        <TypoHeading as="h1">Reset your password</TypoHeading>
        <TypoCaption as="p">Enter your email and we'll send you a reset link.</TypoCaption>
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
