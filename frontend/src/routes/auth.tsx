import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useCallback } from "react";
import { Eye, EyeOff, Github } from "lucide-react";
import { APP_LOGO } from "@/lib/logo";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { LoadingButton } from "@/components/shared/LoadingButton";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in — DevLink" },
      { name: "description", content: "Sign in or create your DevLink account." },
    ],
  }),
  component: AuthScreen,
});

const signInSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});
const signUpSchema = signInSchema
  .extend({
    first_name: z.string().min(2, "At least 2 characters").max(100, "At most 100 characters"),
    last_name: z.string().min(2, "At least 2 characters").max(100, "At most 100 characters"),
    username: z
      .string()
      .min(3, "At least 3 characters")
      .max(50, "At most 50 characters")
      .regex(/^[a-zA-Z0-9_]+$/, "Letters, numbers, and underscores only"),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: "Passwords must match",
    path: ["confirmPassword"],
  });

type SignIn = z.infer<typeof signInSchema>;
type SignUp = z.infer<typeof signUpSchema>;

function AuthScreen() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const signInForm = useForm<SignIn>({ resolver: zodResolver(signInSchema) });
  const signUpForm = useForm<SignUp>({ resolver: zodResolver(signUpSchema) });

  const inp =
    "w-full border border-border rounded-md px-3 py-[8px] text-[14px] text-foreground bg-surface outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground transition-all";
  const err = "mt-1 text-[12px] text-destructive";
  const lbl = "block text-[13px] font-semibold text-foreground mb-1";

  const onSubmit = useCallback(async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
      toast.success(mode === "signin" ? "Signed in" : "Account created");
      navigate({ to: "/dashboard" });
    } finally {
      setSubmitting(false);
    }
  }, [submitting, mode, navigate]);

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center overflow-y-auto bg-background px-4 py-8">
      <Link to="/" className="mb-2 flex items-center gap-2.5">
        <img src={APP_LOGO} alt="DevLink" className="h-12 w-12 rounded-full text-center" />
        <span className="text-[36px] font-bold tracking-tight text-foreground">DevLink</span>
      </Link>

      <div className="w-full max-w-[500px] rounded-md border border-border bg-surface px-8 py-6">
        <button className="mb-3 flex w-full items-center justify-center gap-2.5 rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] font-medium text-foreground hover:bg-muted">
          <Github size={16} /> Continue with GitHub
        </button>
        <button className="mb-4 flex w-full items-center justify-center gap-2.5 rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] font-medium text-foreground hover:bg-muted">
          <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden>
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Continue with Google
        </button>

        <div className="mb-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-[12px] text-muted-foreground">Or</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        {mode === "signin" ? (
          <form onSubmit={signInForm.handleSubmit(onSubmit)} noValidate>
            <div className="mb-4">
              <label className={lbl}>Email</label>
              <input type="email" className={inp} {...signInForm.register("email")} />
              {signInForm.formState.errors.email && (
                <p className={err}>{signInForm.formState.errors.email.message}</p>
              )}
            </div>
            <div className="mb-1">
              <label className={lbl}>Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  className={`${inp} pr-9`}
                  {...signInForm.register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {signInForm.formState.errors.password && (
                <p className={err}>{signInForm.formState.errors.password.message}</p>
              )}
            </div>
            <div className="mb-4 mt-1.5 flex justify-end">
              <Link
                to="/forgot-password"
                className="text-[13px] font-medium text-primary hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <LoadingButton
              type="submit"
              loading={submitting}
              loadingText="Signing In..."
              className="mt-2 w-full py-[9px] text-[14px]"
            >
              Sign In
            </LoadingButton>
          </form>
        ) : (
          <form
            className="max-h-96 overflow-y-auto"
            onSubmit={signUpForm.handleSubmit(onSubmit)}
            noValidate
          >
            <div className="mb-4 grid grid-cols-2 gap-3">
              <div>
                <label className={lbl}>First name</label>
                <input className={inp} {...signUpForm.register("first_name")} />
                {signUpForm.formState.errors.first_name && (
                  <p className={err}>{signUpForm.formState.errors.first_name.message}</p>
                )}
              </div>
              <div>
                <label className={lbl}>Last name</label>
                <input className={inp} {...signUpForm.register("last_name")} />
                {signUpForm.formState.errors.last_name && (
                  <p className={err}>{signUpForm.formState.errors.last_name.message}</p>
                )}
              </div>
            </div>
            <div className="mb-4">
              <label className={lbl}>Username</label>
              <input className={inp} {...signUpForm.register("username")} />
              {signUpForm.formState.errors.username && (
                <p className={err}>{signUpForm.formState.errors.username.message}</p>
              )}
            </div>
            <div className="mb-4">
              <label className={lbl}>Email</label>
              <input type="email" className={inp} {...signUpForm.register("email")} />
              {signUpForm.formState.errors.email && (
                <p className={err}>{signUpForm.formState.errors.email.message}</p>
              )}
            </div>
            <div className="mb-4">
              <label className={lbl}>Password</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  className={`${inp} pr-9`}
                  {...signUpForm.register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {signUpForm.formState.errors.password && (
                <p className={err}>{signUpForm.formState.errors.password.message}</p>
              )}
            </div>
            <div className="mb-4">
              <label className={lbl}>Confirm password</label>
              <div className="relative">
                <input
                  type={showConfirm ? "text" : "password"}
                  className={`${inp} pr-9`}
                  {...signUpForm.register("confirmPassword")}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                >
                  {showConfirm ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {signUpForm.formState.errors.confirmPassword && (
                <p className={err}>{signUpForm.formState.errors.confirmPassword.message}</p>
              )}
            </div>
            <LoadingButton
              type="submit"
              loading={submitting}
              loadingText="Creating Account..."
              className="mt-2 w-full py-[9px] text-[14px]"
            >
              Create account
            </LoadingButton>
          </form>
        )}

        <p className="mt-2 text-center text-[13px] text-muted-foreground">
          {mode === "signin" ? (
            <>
              Don't have an account?{" "}
              <button
                onClick={() => setMode("signup")}
                className="font-medium text-primary hover:underline"
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                onClick={() => setMode("signin")}
                className="font-medium text-primary hover:underline"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>

      <div className="mt-3 flex items-center gap-5">
        {["Privacy", "Security", "Terms", "Status"].map((item) => (
          <a
            key={item}
            href="#"
            className="text-[12px] text-muted-foreground hover:text-primary hover:underline"
          >
            {item}
          </a>
        ))}
      </div>
    </div>
  );
}
