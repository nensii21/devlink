import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Key,
  Copy,
  Download,
  RefreshCw,
  Lock,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { TypoSection, TypoCard } from "@/components/shared/Typography";

export const MFASection: React.FC = () => {
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  // Setup state
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [secret, setSecret] = useState("");
  const [provisioningUri, setProvisioningUri] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Recovery codes state
  const [showCodesModal, setShowCodesModal] = useState(false);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);

  // Disable state
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [disableCode, setDisableCode] = useState("");

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/mfa/status");
      if (res.ok) {
        const data = await res.json();
        setMfaEnabled(data.mfa_enabled);
      }
    } catch {
      toast.error("Failed to load 2FA status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleStartSetup = async () => {
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/auth/mfa/setup", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setSecret(data.secret);
        setProvisioningUri(data.provisioning_uri);
        setShowSetupModal(true);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to initialize 2FA setup");
      }
    } catch {
      toast.error("Error setting up 2FA");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEnableMFA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode || verificationCode.length < 6) {
      toast.error("Please enter a valid 6-digit code.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/auth/mfa/enable", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secret, code: verificationCode }),
      });
      if (res.ok) {
        const data = await res.json();
        setMfaEnabled(true);
        setBackupCodes(data.backup_codes);
        setShowSetupModal(false);
        setShowCodesModal(true);
        setVerificationCode("");
        toast.success("Two-Factor Authentication enabled successfully!");
      } else {
        const err = await res.json();
        toast.error(err.detail || "Verification failed. Check your authenticator app code.");
      }
    } catch {
      toast.error("Error enabling 2FA");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDisableMFA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!disableCode) {
      toast.error("Please enter a verification code.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/auth/mfa/disable", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: disableCode }),
      });
      if (res.ok) {
        setMfaEnabled(false);
        setShowDisableModal(false);
        setDisableCode("");
        toast.success("Two-Factor Authentication disabled.");
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to disable 2FA.");
      }
    } catch {
      toast.error("Error disabling 2FA");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegenerateCodes = async () => {
    const code = prompt("Enter your 6-digit authenticator code to regenerate recovery codes:");
    if (!code) return;
    try {
      const res = await fetch("/api/v1/auth/mfa/recovery-codes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      if (res.ok) {
        const data = await res.json();
        setBackupCodes(data.backup_codes);
        setShowCodesModal(true);
        toast.success("Recovery codes regenerated!");
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to regenerate codes");
      }
    } catch {
      toast.error("Error regenerating recovery codes");
    }
  };

  const copyCodes = () => {
    navigator.clipboard.writeText(backupCodes.join("\n"));
    setCopied(true);
    toast.success("Recovery codes copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadCodes = () => {
    const element = document.createElement("a");
    const file = new Blob([backupCodes.join("\n")], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "devlink-recovery-codes.txt";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="space-y-6 bg-gray-900/40 border border-gray-800 rounded-xl p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <TypoSection>
            <Lock size={18} className="text-indigo-400" /> Two-Factor Authentication (2FA)
          </TypoSection>
          <p className="text-xs text-gray-400">
            Secure your DevLink account using Time-based One-Time Passwords (TOTP) from
            authenticator apps like Google Authenticator or 1Password.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {mfaEnabled ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
              <ShieldCheck size={14} className="text-emerald-400" /> Enabled
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800">
              <ShieldAlert size={14} className="text-amber-400" /> Disabled
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-xs text-gray-500 italic">Checking 2FA status...</div>
      ) : mfaEnabled ? (
        <div className="space-y-4 pt-2">
          <p className="text-xs text-gray-300">
            Your account is protected with Two-Factor Authentication. You will be prompted for an
            authenticator code during login.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleRegenerateCodes}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium bg-gray-800 hover:bg-gray-700 text-white border border-gray-700 transition-colors"
            >
              <RefreshCw size={14} /> Regenerate Recovery Codes
            </button>
            <button
              onClick={() => setShowDisableModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/80 transition-colors"
            >
              Disable 2FA
            </button>
          </div>
        </div>
      ) : (
        <div className="pt-2">
          <button
            onClick={handleStartSetup}
            disabled={submitting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition-colors"
          >
            <ShieldCheck size={16} /> Set Up Two-Factor Authentication
          </button>
        </div>
      )}

      {/* TOTP Setup Modal */}
      {showSetupModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5 shadow-2xl">
            <TypoCard>Set Up Authenticator App</TypoCard>
            <p className="text-xs text-gray-400">
              1. Scan the secret key or enter it into your authenticator app (Google Authenticator,
              Authy, 1Password).
            </p>

            <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 text-center space-y-2">
              <div className="text-xs text-gray-400 font-mono">Secret Key</div>
              <div className="text-base font-mono font-bold text-indigo-400 tracking-wider select-all">
                {secret}
              </div>
            </div>

            <form onSubmit={handleEnableMFA} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  2. Enter 6-digit code from app
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="123456"
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-center text-lg font-mono text-white tracking-widest focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSetupModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg"
                >
                  Verify & Enable
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Recovery Codes Modal */}
      {showCodesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5 shadow-2xl">
            <div className="space-y-1">
              <TypoCard>
                <Key className="text-amber-400" size={18} /> Recovery Codes
              </TypoCard>
              <p className="text-xs text-gray-400">
                Save these single-use recovery codes in a safe place. If you lose your phone, you
                can use one of these codes to log in.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 bg-gray-950 p-4 rounded-lg border border-gray-800 font-mono text-sm text-center text-amber-300">
              {backupCodes.map((code, idx) => (
                <div key={idx} className="bg-gray-900/60 py-1.5 rounded border border-gray-800/60">
                  {code}
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2">
              <div className="flex gap-2">
                <button
                  onClick={copyCodes}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800 text-white hover:bg-gray-700"
                >
                  {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}{" "}
                  Copy
                </button>
                <button
                  onClick={downloadCodes}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800 text-white hover:bg-gray-700"
                >
                  <Download size={14} /> Download
                </button>
              </div>
              <button
                onClick={() => setShowCodesModal(false)}
                className="px-4 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disable Modal */}
      {showDisableModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-sm bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4 shadow-2xl">
            <TypoCard>Disable Two-Factor Authentication</TypoCard>
            <p className="text-xs text-gray-400">
              Enter your current 6-digit authenticator code or a recovery code to confirm disabling
              2FA.
            </p>
            <form onSubmit={handleDisableMFA} className="space-y-4">
              <input
                type="text"
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value)}
                placeholder="Authenticator or Recovery Code"
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-center text-sm font-mono text-white focus:outline-none focus:border-indigo-500"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowDisableModal(false)}
                  className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white rounded-lg"
                >
                  Confirm Disable
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
