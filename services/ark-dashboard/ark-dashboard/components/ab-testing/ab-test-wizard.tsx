"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent
} from "@/components/ui/dialog";
import { ABConfigureStep } from "./ab-configure-step";
import { ABPreviewStep } from "./ab-preview-step";
import { ABResultsStep } from "./ab-results-step";
import type { ABExperiment, ABExperimentModifications } from "@/lib/types/ab-experiment";

interface ABTestWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  queryNamespace: string;
  queryName: string;
  baselineQuery: unknown;
}

type WizardStep = "configure" | "preview" | "results";

export function ABTestWizard({
  open,
  onOpenChange,
  queryNamespace,
  queryName,
  baselineQuery
}: ABTestWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>("configure");
  const [modifications, setModifications] = useState<ABExperimentModifications>({});
  const [experiment, setExperiment] = useState<ABExperiment | null>(null);

  const handleConfigureComplete = (mods: ABExperimentModifications) => {
    setModifications(mods);
    setCurrentStep("preview");
  };

  const handlePreviewBack = () => {
    setCurrentStep("configure");
  };

  const handlePreviewConfirm = (exp: ABExperiment) => {
    setExperiment(exp);
    setCurrentStep("results");
  };

  const handleResultsClose = () => {
    setCurrentStep("configure");
    setModifications({});
    setExperiment(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] sm:!max-w-[1400px] max-h-[95vh] overflow-y-auto">
        {currentStep === "configure" && (
          <ABConfigureStep
            baselineQuery={baselineQuery}
            onComplete={handleConfigureComplete}
            onCancel={() => onOpenChange(false)}
          />
        )}

        {currentStep === "preview" && (
          <ABPreviewStep
            namespace={queryNamespace}
            queryName={queryName}
            baselineQuery={baselineQuery}
            modifications={modifications}
            onBack={handlePreviewBack}
            onConfirm={handlePreviewConfirm}
          />
        )}

        {currentStep === "results" && experiment && (
          <ABResultsStep
            namespace={queryNamespace}
            queryName={queryName}
            experiment={experiment}
            onClose={handleResultsClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
