"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import {
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import type { ABExperimentModifications, ABExperimentTargetType } from "@/lib/types/ab-experiment";
import { useGetAllModels } from "@/lib/services/models-hooks";
import { useGetAllAgents, useGetAgent } from "@/lib/services/agents-hooks";

interface ABConfigureStepProps {
  baselineQuery: unknown;
  onComplete: (modifications: ABExperimentModifications) => void;
  onCancel: () => void;
}

export function ABConfigureStep({
  baselineQuery,
  onComplete,
  onCancel
}: ABConfigureStepProps) {
  const [selectedComponent, setSelectedComponent] = useState<"query" | "agents" | "teams">("query");
  const [experimentInput, setExperimentInput] = useState("");
  const [targetType, setTargetType] = useState<ABExperimentTargetType>("agent");
  const [targetName, setTargetName] = useState("");
  const [experimentTargetName, setExperimentTargetName] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [instructions, setInstructions] = useState("");
  const [validationError, setValidationError] = useState("");

  const { data: modelsData } = useGetAllModels();
  const { data: agentsData } = useGetAllAgents();
  const { data: baselineAgent } = useGetAgent(targetName);
  const { data: experimentAgent } = useGetAgent(experimentTargetName);

  useEffect(() => {
    const query = baselineQuery as Record<string, unknown>;
    const input = query?.input;
    const targets = query?.targets as Array<{ name?: string; type?: string }> | undefined;

    if (input) {
      setExperimentInput(
        typeof input === "string"
          ? input
          : JSON.stringify(input, null, 2)
      );
    }

    if (targets && Array.isArray(targets) && targets.length > 0) {
      const firstTarget = targets[0];
      const name = firstTarget.name || "";
      setTargetName(name);
      setExperimentTargetName(name);
      setTargetType(firstTarget.type === "team" ? "team" : "agent");
    }
  }, [baselineQuery]);

  useEffect(() => {
    if (experimentAgent?.prompt) {
      setInstructions(experimentAgent.prompt);
    }
    if (experimentAgent?.modelRef?.name) {
      setSelectedModel(experimentAgent.modelRef.name);
    }
  }, [experimentAgent]);

  const validateSelection = (): boolean => {
    setValidationError("");

    if (selectedComponent === "agents" || selectedComponent === "teams") {
      const query = baselineQuery as Record<string, unknown>;
      const targets = (query?.targets as Array<{ type?: string }> | undefined) || [];

      if (targets.length === 0) {
        setValidationError("Baseline query must have at least one target");
        return false;
      }

      if (targets.length > 1) {
        setValidationError("A/B testing only supports queries with a single agent or team target");
        return false;
      }

      const targetTypes = new Set(targets.map((t) => t.type));
      if (targetTypes.size > 1 || (!targetTypes.has("agent") && !targetTypes.has("team"))) {
        setValidationError("Target must be either a single agent or a single team");
        return false;
      }
    }

    if (selectedComponent === "teams") {
      setValidationError("Team A/B testing is not yet supported");
      return false;
    }

    return true;
  };

  const handleNext = () => {
    if (!validateSelection()) {
      return;
    }

    const query = baselineQuery as Record<string, unknown>;
    const modifications: ABExperimentModifications = {};

    if (selectedComponent === "query" && experimentInput !== query?.input) {
      modifications.input = experimentInput;
    }

    if (selectedComponent === "agents" && experimentTargetName) {
      modifications.targetType = targetType;
      modifications.targetName = experimentTargetName;
      modifications.targetChanges = {};

      if (selectedModel) {
        modifications.targetChanges.model = selectedModel;
      }

      if (instructions) {
        modifications.targetChanges.instructions = instructions;
      }
    }

    if (Object.keys(modifications).length === 0) {
      setValidationError("Please make at least one modification to create an experiment");
      return;
    }

    onComplete(modifications);
  };

  const query = baselineQuery as Record<string, unknown>;
  const input = query?.input;
  const baselineInput = typeof input === "string"
    ? input
    : JSON.stringify(input, null, 2);

  return (
    <>
      <DialogHeader>
        <DialogTitle>Configure A/B Test</DialogTitle>
        <DialogDescription>
          Modify the query or agent configuration to test against the baseline
        </DialogDescription>
      </DialogHeader>

      <div className="flex gap-6">
        <div className="w-48 flex-shrink-0 border-r pr-4">
          <Label className="text-sm font-medium mb-3 block">Component</Label>
          <div className="flex flex-col gap-2">
            <Button
              variant={selectedComponent === "query" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedComponent("query")}
              className="w-full justify-start"
            >
              Query
            </Button>
            <Button
              variant={selectedComponent === "agents" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedComponent("agents")}
              className="w-full justify-start"
            >
              Agents
            </Button>
            <Button
              variant={selectedComponent === "teams" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedComponent("teams")}
              className="w-full justify-start"
            >
              Teams
            </Button>
          </div>
        </div>

        <div className="flex-1 grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium mb-2 block">Baseline (Read-only)</Label>
            {selectedComponent === "query" && (
              <div className="space-y-2">
                <Label className="text-xs">Input</Label>
                <Textarea
                  value={baselineInput}
                  readOnly
                  className="min-h-[300px] bg-muted text-sm font-mono"
                />
              </div>
            )}
            {selectedComponent === "agents" && (
              <div className="space-y-4">
                <div>
                  <Label className="text-xs">Target Agent</Label>
                  <div className="mt-1 p-2 bg-muted rounded text-sm font-medium">
                    {targetName || "No agent target"}
                  </div>
                </div>
                <div>
                  <Label className="text-xs">Model</Label>
                  <div className="mt-1 p-2 bg-muted rounded text-sm truncate">
                    {baselineAgent?.modelRef?.name || "Default"}
                  </div>
                </div>
                <div>
                  <Label className="text-xs">System Prompt</Label>
                  <Textarea
                    value={baselineAgent?.prompt || ""}
                    readOnly
                    className="min-h-[100px] bg-muted text-sm"
                  />
                </div>
              </div>
            )}
            {selectedComponent === "teams" && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Team A/B testing is not yet supported
                </AlertDescription>
              </Alert>
            )}
          </div>

          <div>
            <Label className="text-sm font-medium mb-2 block">Experiment (Editable)</Label>
            {selectedComponent === "query" && (
              <div className="space-y-2">
                <Label className="text-xs">Input</Label>
                <Textarea
                  value={experimentInput}
                  onChange={(e) => setExperimentInput(e.target.value)}
                  className="min-h-[300px] text-sm font-mono"
                  placeholder="Modify the query input..."
                />
              </div>
            )}
            {selectedComponent === "agents" && (
              <div className="space-y-4">
                <div>
                  <Label className="text-xs">Target Agent</Label>
                  <Select value={experimentTargetName} onValueChange={setExperimentTargetName}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select agent" />
                    </SelectTrigger>
                    <SelectContent>
                      {agentsData?.map((agent) => (
                        <SelectItem key={agent.name} value={agent.name}>
                          {agent.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">Model</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {modelsData?.map((model) => (
                        <SelectItem key={model.name} value={model.name}>
                          {model.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-xs">System Prompt</Label>
                  <Textarea
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    className="min-h-[100px]"
                    placeholder="Custom system prompt..."
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {validationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{validationError}</AlertDescription>
        </Alert>
      )}

      <DialogFooter>
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleNext}>
          Next: Preview
        </Button>
      </DialogFooter>
    </>
  );
}
