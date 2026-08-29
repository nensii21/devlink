import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { projectsApi } from "@/api/modules/projects";
import { toast } from "sonner";

interface AIDescriptionGeneratorProps {
  onGenerated: (description: string) => void;
}

export function AIDescriptionGenerator({ onGenerated }: AIDescriptionGeneratorProps) {
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Please enter a short prompt to generate a description.");
      return;
    }

    setIsGenerating(true);
    try {
      const { description } = await projectsApi.generateDescription(prompt);
      onGenerated(description);
      toast.success("Description generated successfully!");
      setPrompt("");
    } catch (error) {
      console.error("Failed to generate description:", error);
      toast.error("Failed to generate description. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
      <div>
        <Label htmlFor="ai-prompt" className="text-sm font-medium flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          AI Description Generator
        </Label>
        <p className="text-xs text-muted-foreground mt-1 mb-3">
          Describe your project idea briefly, and our AI will generate a comprehensive description
          for you.
        </p>
      </div>
      <div className="flex gap-2">
        <Input
          id="ai-prompt"
          placeholder="e.g. A real-time chat application for developers..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleGenerate();
            }
          }}
          disabled={isGenerating}
          className="flex-1"
        />
        <Button
          type="button"
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          variant="secondary"
        >
          {isGenerating ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 h-4 w-4" />
          )}
          Generate
        </Button>
      </div>
    </div>
  );
}
