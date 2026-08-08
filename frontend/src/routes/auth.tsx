import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useCallback, useEffect } from "react";
import { Eye, EyeOff, Github, Linkedin } from "lucide-react";
import { APP_LOGO } from "@/lib/logo";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { LoadingButton } from "@/components/shared/LoadingButton";
import { authApi } from "@/api/modules/auth";
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
  password: z.string().min(6, "At least 6 characters"),
});
const signUpSchema = signInSchema
  .extend({
    firstName: z.string().min(1, "Required").max(50),
    lastName: z.string().min(1, "Required").max(50),
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
  const [oauthLoading, setOauthLoading] = useState<"github" | "linkedin" | null>(null);

  const signInForm = useForm<SignIn>({ resolver: zodResolver(signInSchema) });
  const signUpForm = useForm<SignUp>({ resolver: zodResolver(signUpSchema) });

  const inp =
    "w-full border border-border rounded-md px-3 py-[8px] text-[14px] text-foreground bg-surface outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 placeholder:text-muted-foreground transition-all";
  const err = "mt-1 text-[12px] text-destructive";
  const lbl = "block text-[13px] font-semibold text-foreground mb-1";

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const provider = sessionStorage.getItem("devlink.oauth.provider");
    if (!code || !provider) return;
    const finishOauth =
      provider === "linkedin"
        ? authApi.linkedinLogin(code, state ?? "")
        : authApi.githubLogin(code, state ?? "");
    finishOauth
      .then(() => {
        sessionStorage.removeItem("devlink.oauth.provider");
        toast.success("Signed in successfully");
        navigate({ to: "/dashboard" });
      })
      .catch(() => toast.error("Sign-in failed. Please try again."));
  }, [navigate]);

  const beginOAuth = useCallback(async (provider: "github" | "linkedin") => {
    setOauthLoading(provider);
    try {
      const { state } = await authApi.oauthAuthorize(provider);
      sessionStorage.setItem("devlink.oauth.provider", provider);
      const redirectUri = window.location.origin + "/auth";
      if (provider === "linkedin") {
        const params = new URLSearchParams({
          response_type: "code",
          client_id: import.meta.env.VITE_LINKEDIN_CLIENT_ID ?? "",
          redirect_uri: redirectUri,
          scope: "openid profile email",
          state,
        });
        window.location.href = `https://www.linkedin.com/oauth/v2/authorization?${params}`;
      } else {
        const params = new URLSearchParams({
          client_id: import.meta.env.VITE_GITHUB_CLIENT_ID ?? "",
          redirect_uri: redirectUri,
          scope: "read:user user:email",
          state,
        });
        window.location.href = `https://github.com/login/oauth/authorize?${params}`;
      }
    } catch {
      setOauthLoading(null);
      toast.error("Unable to start sign-in. Please try again.");
    }
  }, []);
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
        <button
          type="button"
          disabled={oauthLoading !== null}
          onClick={() => beginOAuth("github")}
          className="mb-3 flex w-full items-center justify-center gap-2.5 rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] font-medium text-foreground hover:bg-muted disabled:opacity-60"
        >
          {oauthLoading === "github" ? (
            "Redirecting..."
          ) : (
            <>
              <Github size={16} /> Continue with GitHub
            </>
          )}
        </button>
        <button
          type="button"
          disabled={oauthLoading !== null}
          onClick={() => beginOAuth("linkedin")}
          className="mb-4 flex w-full items-center justify-center gap-2.5 rounded-md border border-border bg-surface px-3 py-[8px] text-[14px] font-medium text-foreground hover:bg-muted disabled:opacity-60"
        >
          {oauthLoading === "linkedin" ? (
            "Redirecting..."
          ) : (
            <>
              <Linkedin size={16} /> Continue with LinkedIn
            </>
          )}
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
                <input className={inp} {...signUpForm.register("firstName")} />
                {signUpForm.formState.errors.firstName && (
                  <p className={err}>{signUpForm.formState.errors.firstName.message}</p>
                )}
              </div>
              <div>
                <label className={lbl}>Last name</label>
                <input className={inp} {...signUpForm.register("lastName")} />
                {signUpForm.formState.errors.lastName && (
                  <p className={err}>{signUpForm.formState.errors.lastName.message}</p>
                )}
              </div>
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
