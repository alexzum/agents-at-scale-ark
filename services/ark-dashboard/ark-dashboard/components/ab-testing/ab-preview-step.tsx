"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, CheckCircle2, Activity } from "lucide-react";
import type { ABExperiment, ABExperimentModifications } from "@/lib/types/ab-experiment";
import { abExperimentsService } from "@/lib/services/ab-experiments";
import { evaluatorsService, type EvaluatorDetailResponse } from "@/lib/services";

interface ABPreviewStepProps {
  namespace: string;
  queryName: string;
  baselineQuery: unknown;
  modifications: ABExperimentModifications;
  onBack: () => void;
  onConfirm: (experiment: ABExperiment) => void;
}

export function ABPreviewStep({
  namespace,
  queryName,
  baselineQuery,
  modifications,
  onBack,
  onConfirm
}: ABPreviewStepProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evaluators, setEvaluators] = useState<EvaluatorDetailResponse[]>([]);
  const [loadingEvaluators, setLoadingEvaluators] = useState(true);

  const query = baselineQuery as Record<string, unknown>;
  const metadata = query?.metadata as Record<string, unknown> | undefined;
  const labels = (metadata?.labels as Record<string, string>) || {};
  const evaluatorLabels = labels;
  const willTriggerEvaluators = Object.keys(evaluatorLabels).length > 0;

  useEffect(() => {
    const loadEvaluators = async () => {
      try {
        const basicEvaluators = await evaluatorsService.getAll();
        const detailedEvaluators = await Promise.all(
          basicEvaluators.map(async (evaluator) => {
            const details = await evaluatorsService.getDetailsByName(evaluator.name);
            return details;
          })
        );
        setEvaluators(detailedEvaluators.filter((e) => e !== null) as EvaluatorDetailResponse[]);
      } catch (err) {
        console.error("Failed to load evaluators:", err);
      } finally {
        setLoadingEvaluators(false);
      }
    };

    loadEvaluators();
  }, []);

  const matchingQualityEvaluators = evaluators.filter((evaluator) => {
    const address = evaluator.spec?.address as { valueFrom?: { serviceRef?: { path?: string } } } | undefined;
    const serviceRefPath = address?.valueFrom?.serviceRef?.path;
    const evaluatorLabels = evaluator.metadata?.labels as Record<string, string> | undefined;
    const isMetricsEvaluator = serviceRefPath === "/evaluate-metrics" ||
                               evaluatorLabels?.type?.includes("metrics");
    if (isMetricsEvaluator) return false;

    const selector = evaluator.spec?.selector as { matchLabels?: Record<string, string> } | undefined;
    if (!selector || Object.keys(selector).length === 0) return false;

    const matchLabels = selector.matchLabels || (selector as Record<string, string>);
    return Object.entries(matchLabels).every(([key, value]) => {
      return labels[key] === value;
    });
  });

  const matchingMetricsEvaluators = evaluators.filter((evaluator) => {
    const address = evaluator.spec?.address as { valueFrom?: { serviceRef?: { path?: string } } } | undefined;
    const serviceRefPath = address?.valueFrom?.serviceRef?.path;
    const evaluatorLabels = evaluator.metadata?.labels as Record<string, string> | undefined;
    const isMetricsEvaluator = serviceRefPath === "/evaluate-metrics" ||
                               evaluatorLabels?.type?.includes("metrics");
    if (!isMetricsEvaluator) return false;

    const selector = evaluator.spec?.selector as { matchLabels?: Record<string, string> } | undefined;
    if (!selector || Object.keys(selector).length === 0) return false;

    const matchLabels = selector.matchLabels || (selector as Record<string, string>);
    return Object.entries(matchLabels).every(([key, value]) => {
      return labels[key] === value;
    });
  });

  const willTriggerMetrics = matchingMetricsEvaluators.length > 0;

  const handleConfirm = async () => {
    setIsCreating(true);
    setError(null);

    try {
      const experiment = await abExperimentsService.create(namespace, queryName, {
        modifications,
        createdBy: "dashboard-user"
      });

      onConfirm(experiment);
    } catch (err) {
      const error = err as Error;
      setError(error.message || "Failed to create experiment");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Preview Changes</DialogTitle>
        <DialogDescription>
          Review the changes before running the A/B test
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-6">
        <div>
          <h3 className="font-medium mb-3">Modifications</h3>
          <div className="space-y-2 rounded-lg border p-4">
            {modifications.input && (
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline">Query Input</Badge>
                  <span className="text-sm text-muted-foreground">Modified</span>
                </div>
                <div className="mt-2 space-y-2">
                  <div>
                    <div className="text-xs text-muted-foreground">Baseline:</div>
                    <div className="mt-1 p-2 bg-muted rounded text-sm max-h-20 overflow-y-auto">
                      {typeof query?.input === "string"
                        ? query.input
                        : JSON.stringify(query?.input)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Experiment:</div>
                    <div className="mt-1 p-2 bg-green-50 dark:bg-green-950 rounded text-sm max-h-20 overflow-y-auto">
                      {modifications.input}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {modifications.targetType === "agent" && modifications.targetName && (
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline">Agent Configuration</Badge>
                  <span className="text-sm text-muted-foreground">Modified</span>
                </div>
                <div className="mt-2 space-y-3">
                  <div>
                    <div className="text-xs font-medium">Target Agent</div>
                    <div className="text-sm">{modifications.targetName}</div>
                  </div>

                  {modifications.targetChanges?.model && (
                    <div>
                      <div className="text-xs text-muted-foreground">Model:</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm p-1 px-2 bg-muted rounded">
                          {((query?.parameters as Array<{ name?: string; value?: string }> | undefined)?.find((p) => p.name === "model")?.value) || "Default"}
                        </span>
                        <span className="text-muted-foreground">→</span>
                        <span className="text-sm p-1 px-2 bg-green-50 dark:bg-green-950 rounded font-medium">
                          {modifications.targetChanges.model}
                        </span>
                      </div>
                    </div>
                  )}

                  {modifications.targetChanges?.instructions && (
                    <div>
                      <div className="text-xs text-muted-foreground">Instructions:</div>
                      <div className="mt-1 p-2 bg-green-50 dark:bg-green-950 rounded text-sm max-h-20 overflow-y-auto">
                        {modifications.targetChanges.instructions}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <h3 className="font-medium mb-3">Evaluation Status</h3>
          <div className="space-y-3">
            <div className="rounded-lg border p-4">
              {willTriggerEvaluators ? (
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium">Quality Evaluators</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {loadingEvaluators ? (
                        "Loading evaluators..."
                      ) : matchingQualityEvaluators.length > 0 ? (
                        <>
                          {matchingQualityEvaluators.length} evaluator(s) will assess quality
                          <div className="mt-2 flex flex-wrap gap-2">
                            {matchingQualityEvaluators.map((evaluator) => (
                              <Badge key={evaluator.name} variant="secondary" className="text-xs">
                                {evaluator.name}
                              </Badge>
                            ))}
                          </div>
                        </>
                      ) : (
                        "No quality evaluators match the query labels"
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium">No evaluators configured</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      Add evaluation labels to the baseline query to enable automatic evaluation
                    </div>
                  </div>
                </div>
              )}
            </div>

            {willTriggerEvaluators && (
              <div className={`rounded-lg border p-4 ${!willTriggerMetrics ? "opacity-50" : ""}`}>
                <div className="flex items-start gap-3">
                  {willTriggerMetrics ? (
                    <Activity className="h-5 w-5 text-blue-600 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-gray-400 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className="font-medium">Performance Metrics</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {loadingEvaluators ? (
                        "Loading evaluators..."
                      ) : willTriggerMetrics ? (
                        <>
                          {matchingMetricsEvaluators.length} metrics evaluator(s) will assess cost and execution time
                          <div className="mt-2 flex flex-wrap gap-2">
                            {matchingMetricsEvaluators.map((evaluator) => (
                              <Badge key={evaluator.name} variant="secondary" className="text-xs">
                                {evaluator.name}
                              </Badge>
                            ))}
                          </div>
                        </>
                      ) : (
                        "No metrics evaluators match (performance comparison will be limited)"
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <h3 className="font-medium mb-3">Cost Estimate</h3>
          <div className="rounded-lg border p-4">
            <Alert>
              <AlertDescription>
                This experiment will run 2 queries (baseline + experiment) with associated evaluation costs
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <DialogFooter>
        <Button variant="outline" onClick={onBack} disabled={isCreating}>
          Back
        </Button>
        <Button onClick={handleConfirm} disabled={isCreating}>
          {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isCreating ? "Creating..." : "Run Experiment"}
        </Button>
      </DialogFooter>
    </>
  );
}
