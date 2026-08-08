import React from "react";
import { type CreateProjectFormData } from "@/lib/schemas/forms";
import { Zap, Rocket, Globe, FlaskConical, Briefcase } from "lucide-react";
import { cn } from "@/lib/utils";

export type ProjectTemplate = {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  fields: Partial<CreateProjectFormData>;
};

const templates: ProjectTemplate[] = [
  {
    id: "hackathon",
    name: "Hackathon",
    icon: <Zap size={18} className="text-amber-500" />,
    description: "Fast-paced project built for a hackathon.",
    fields: {
      stage: "idea",
      max_team_size: 4,
      description: "A fast-paced project built for a hackathon. We need to move quickly and build an MVP.",
    },
  },
  {
    id: "startup",
    name: "Startup",
    icon: <Rocket size={18} className="text-blue-500" />,
    description: "A new venture aiming to build a scalable product.",
    fields: {
      stage: "in_development",
      max_team_size: 10,
      description: "A new startup venture aiming to build a scalable product.",
    },
  },
  {
    id: "open-source",
    name: "Open Source",
    icon: <Globe size={18} className="text-emerald-500" />,
    description: "An open-source library or tool.",
    fields: {
      stage: "in_development",
      max_team_size: 100,
      description: "An open-source library or tool. Contributions are welcome!",
      tech_stack: "TypeScript, Node.js, React",
    },
  },
  {
    id: "research",
    name: "Research",
    icon: <FlaskConical size={18} className="text-purple-500" />,
    description: "An exploratory research project.",
    fields: {
      stage: "idea",
      max_team_size: 5,
      description: "An exploratory research project to test new ideas and concepts.",
    },
  },
  {
    id: "portfolio",
    name: "Portfolio",
    icon: <Briefcase size={18} className="text-slate-500" />,
    description: "Personal portfolio or side project.",
    fields: {
      stage: "in_development",
      max_team_size: 1,
      description: "A personal portfolio project to showcase skills and experience.",
    },
  },
];

interface ProjectTemplateSelectProps {
  onSelect: (fields: Partial<CreateProjectFormData>) => void;
  selectedTemplateId?: string;
  onTemplateIdChange: (id: string) => void;
}

export function ProjectTemplateSelect({ onSelect, selectedTemplateId, onTemplateIdChange }: ProjectTemplateSelectProps) {
  return (
    <div className="space-y-2">
      <label className="text-[12px] font-semibold text-muted-foreground uppercase">
        Start from a Template
      </label>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {templates.map((template) => {
          const isSelected = selectedTemplateId === template.id;
          return (
            <button
              key={template.id}
              type="button"
              onClick={() => {
                onTemplateIdChange(template.id);
                onSelect(template.fields);
              }}
              className={cn(
                "flex flex-col items-start p-3 text-left rounded-xl transition-all border",
                isSelected
                  ? "border-primary bg-primary/10 shadow-sm ring-1 ring-primary/20"
                  : "border-border bg-surface hover:border-primary/50 hover:bg-muted"
              )}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <div className={cn("p-1.5 rounded-md", isSelected ? "bg-background" : "bg-muted")}>
                  {template.icon}
                </div>
                <span className={cn("font-semibold text-[13px]", isSelected ? "text-primary" : "text-foreground")}>
                  {template.name}
                </span>
              </div>
              <p className={cn("text-[11px] leading-snug line-clamp-2", isSelected ? "text-primary/80" : "text-muted-foreground")}>
                {template.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
