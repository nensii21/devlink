import { Card, EmptyState } from "@/components/shared/primitives";
import { Award, ExternalLink, Calendar, ShieldCheck } from "lucide-react";
import { TypoCaption, TypoHeading } from "@/components/shared/Typography";

export interface CertificationEntry {
  id?: string;
  name: string;
  issuer: string;
  issueDate?: string;
  expiryDate?: string;
  credentialId?: string;
  credentialUrl?: string;
}

export interface CertificationsCardProps {
  certifications?: CertificationEntry[];
}

export function CertificationsCard({ certifications = [] }: CertificationsCardProps) {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-center gap-2.5 mb-3.5">
        <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500">
          <Award size={16} />
        </div>
        <div>
          <TypoHeading as="h2">Certifications & Licenses</TypoHeading>
          <TypoCaption as="p">Verified credentials and industry certifications</TypoCaption>
        </div>
      </div>

      {certifications.length === 0 ? (
        <EmptyState
          icon={Award}
          title="No certifications added yet"
          desc="Add your professional certifications, cloud licenses, or specialized training."
          className="rounded-xl border border-dashed border-primary/20 bg-primary/5 py-6"
        />
      ) : (
        <div className="space-y-2.5">
          {certifications.map((cert, idx) => (
            <div
              key={cert.id || idx}
              className="flex items-start justify-between gap-3 rounded-lg border border-border/70 bg-card p-3 transition-colors hover:border-primary/40"
            >
              <div className="space-y-1 min-w-0 flex-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <p className="text-xs font-bold text-foreground truncate">{cert.name}</p>
                  <span className="inline-flex items-center gap-1 rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                    <ShieldCheck size={10} /> Verified
                  </span>
                </div>
                <p className="text-[11px] font-medium text-muted-foreground">{cert.issuer}</p>
                {cert.issueDate && (
                  <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-mono">
                    <Calendar size={10} /> Issued: {cert.issueDate}
                  </div>
                )}
                {cert.credentialId && (
                  <p className="text-[10px] text-muted-foreground/80 font-mono">
                    ID: {cert.credentialId}
                  </p>
                )}
              </div>

              {cert.credentialUrl && (
                <a
                  href={cert.credentialUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-1 text-[10px] font-medium text-foreground hover:bg-muted transition-colors shrink-0"
                >
                  <span>Verify</span>
                  <ExternalLink size={10} />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default CertificationsCard;
