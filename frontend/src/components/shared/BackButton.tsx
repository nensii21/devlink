import { ArrowLeft } from "lucide-react";
import { Link } from "@tanstack/react-router";

type BackButtonProps = {
  to: string;
  label: string;
};

export function BackButton({ to, label }: BackButtonProps) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 text-[13px] font-medium text-primary hover:underline"
    >
      <ArrowLeft size={14} />
      {label}
    </Link>
  );
}