"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle, Trophy, TrendingUp, TrendingDown, CheckCircle2, Clock } from "lucide-react";
import type { ABExperiment } from "@/lib/types/ab-experiment";
import { abExperimentsService } from "@/lib/services/ab-experiments";
import { useGetEvaluations } from "@/lib/services/evaluations-hooks";

interface ABResultsStepProps {
  namespace: string;
  queryName: string;
  experiment: ABExperiment;
  onClose: () => void;
}

export function ABResultsStep({
  namespace,
  queryName,
  experiment: initialExperiment,
  onClose
}: ABResultsStepProps) {
  const [experiment, setExperiment] = useState(initialExperiment);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: baselineEvaluations, refetch: refetchBaseline } = useGetEvaluations({
    namespace,
    labelSelector: `ark.mckinsey.com/query=${queryName}`
  });

  const { data: variantEvaluations, refetch: refetchVariant } = useGetEvaluations({
    namespace,
    labelSelector: `ark.mckinsey.com/query=${experiment.variantQuery}`
  });

  useEffect(() => {
    if (experiment.status === "pending" || experiment.status === "running") {
      const interval = setInterval(() => {
        refetchBaseline();
        refetchVariant();
      }, 2000);

      abExperimentsService.streamExperimentStatus(
        namespace,
        queryName,
        experiment.id,
        (updatedExperiment) => {
          setExperiment(updatedExperiment);
        }
      );

      return () => clearInterval(interval);
    }
  }, [namespace, queryName, experiment.id, experiment.status, experiment.variantQuery, refetchBaseline, refetchVariant]);

  const handleApplyWinner = async () => {
    if (!experiment.results) return;
    if (experiment.results.winner === "tie") {
      setError("Cannot apply a tie result. Please review manually.");
      return;
    }

    setIsApplying(true);
    setError(null);

    try {
      await abExperimentsService.applyWinner(namespace, queryName, experiment.id, {
        winner: experiment.results.winner
      });

      onClose();
    } catch (err) {
      const error = err as Error;
      setError(error.message || "Failed to apply winner");
    } finally {
      setIsApplying(false);
    }
  };

  const isLoading = experiment.status === "pending" || experiment.status === "running";
  const results = experiment.results;

  return (
    <>
      <DialogHeader>
        <DialogTitle>Experiment Results</DialogTitle>
        <DialogDescription>
          {isLoading
            ? "Waiting for evaluations to complete..."
            : "Compare baseline and experiment performance"}
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Status</h3>
            <Badge variant={
              experiment.status === "completed" ? "default" :
              experiment.status === "failed" ? "destructive" :
              "secondary"
            }>
              {experiment.status}
            </Badge>
          </div>

          {isLoading && (
            <Alert>
              <Loader2 className="h-4 w-4 animate-spin" />
              <AlertDescription>
                <div className="mb-3">Running experiment and evaluations...</div>
                {experiment.variantQuery && (
                  <div className="space-y-3">
                    <div className="text-xs space-y-1">
                      <div className="font-medium">Variant query: {experiment.variantQuery}</div>
                      {experiment.variantAgent && (
                        <div className="font-medium">Variant agent: {experiment.variantAgent}</div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <div className="font-medium mb-2">Baseline Evaluations</div>
                        {baselineEvaluations && baselineEvaluations.length > 0 ? (
                          <div className="space-y-1">
                            {baselineEvaluations.map((evaluation) => (
                              <div key={evaluation.name} className="flex items-center gap-2">
                                {evaluation.phase === "done" ? (
                                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                                ) : (
                                  <Clock className="h-3 w-3 text-yellow-600 animate-pulse" />
                                )}
                                <span className="truncate">{evaluation.name}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-muted-foreground">No evaluations yet...</div>
                        )}
                      </div>

                      <div>
                        <div className="font-medium mb-2">Variant Evaluations</div>
                        {variantEvaluations && variantEvaluations.length > 0 ? (
                          <div className="space-y-1">
                            {variantEvaluations.map((evaluation) => (
                              <div key={evaluation.name} className="flex items-center gap-2">
                                {evaluation.phase === "done" ? (
                                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                                ) : (
                                  <Clock className="h-3 w-3 text-yellow-600 animate-pulse" />
                                )}
                                <span className="truncate">{evaluation.name}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-muted-foreground">No evaluations yet...</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}

          {experiment.status === "failed" && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Experiment failed. Please check query and evaluation logs.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {results && (
          <>
            <div>
              <h3 className="font-medium mb-4">Overall Comparison</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className={`rounded-lg border p-4 ${results.winner === "baseline" ? "ring-2 ring-green-500" : ""}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">Baseline</h4>
                    {results.winner === "baseline" && <Trophy className="h-5 w-5 text-green-600" />}
                  </div>
                  <div className="text-3xl font-bold">{(results.baseline.overallScore * 100).toFixed(1)}%</div>
                  {results.baseline.cost != null && (
                    <div className="text-sm text-muted-foreground mt-2">
                      Cost: ${results.baseline.cost.toFixed(4)}
                    </div>
                  )}
                  {results.baseline.latency != null && (
                    <div className="text-sm text-muted-foreground">
                      Latency: {results.baseline.latency.toFixed(2)}s
                    </div>
                  )}
                </div>

                <div className={`rounded-lg border p-4 ${results.winner === "experiment" ? "ring-2 ring-green-500" : ""}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">Experiment</h4>
                    {results.winner === "experiment" && <Trophy className="h-5 w-5 text-green-600" />}
                  </div>
                  <div className="text-3xl font-bold">{(results.experiment.overallScore * 100).toFixed(1)}%</div>
                  {results.improvement !== 0 && (
                    <div className={`flex items-center gap-1 mt-2 ${results.improvement > 0 ? "text-green-600" : "text-red-600"}`}>
                      {results.improvement > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                      <span className="font-medium">{Math.abs(results.improvement * 100).toFixed(1)}%</span>
                    </div>
                  )}
                  {results.experiment.cost != null && (
                    <div className="text-sm text-muted-foreground">
                      Cost: ${results.experiment.cost.toFixed(4)}
                    </div>
                  )}
                  {results.experiment.latency != null && (
                    <div className="text-sm text-muted-foreground">
                      Latency: {results.experiment.latency.toFixed(2)}s
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-medium mb-4">Criteria Breakdown</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Criterion</TableHead>
                    <TableHead className="text-right">Baseline</TableHead>
                    <TableHead className="text-right">Experiment</TableHead>
                    <TableHead className="text-right">Difference</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.keys(results.baseline.criteria).map((criterion) => {
                    const baselineScore = results.baseline.criteria[criterion] ?? 0;
                    const experimentScore = results.experiment.criteria[criterion] ?? 0;
                    const diff = experimentScore - baselineScore;

                    return (
                      <TableRow key={criterion}>
                        <TableCell className="font-medium capitalize">{criterion}</TableCell>
                        <TableCell className="text-right">{(baselineScore * 100).toFixed(0)}%</TableCell>
                        <TableCell className="text-right">{(experimentScore * 100).toFixed(0)}%</TableCell>
                        <TableCell className={`text-right ${diff > 0 ? "text-green-600" : diff < 0 ? "text-red-600" : ""}`}>
                          {diff > 0 ? "+" : ""}{(diff * 100).toFixed(0)}%
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <DialogFooter>
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
        {results && results.winner === "experiment" && (
          <Button onClick={handleApplyWinner} disabled={isApplying}>
            {isApplying && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isApplying ? "Applying..." : "Apply Winner"}
          </Button>
        )}
      </DialogFooter>
    </>
  );
}
