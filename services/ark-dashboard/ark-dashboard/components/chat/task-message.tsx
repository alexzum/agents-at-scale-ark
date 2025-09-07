"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { a2aTaskService } from "@/lib/services";
import type { A2ATaskDetailResponse } from "@/lib/services";
import { useMarkdownProcessor } from "@/lib/hooks/use-markdown-processor";
import { AlertCircle, Clock, CheckCircle2, XCircle } from "lucide-react";
import { TypingLoader } from "../ui/typing-loader";

interface TaskMessageProps {
  taskId: string;
  namespace: string;
  viewMode?: "text" | "markdown";
}

export function TaskMessage({
  taskId,
  namespace,
  viewMode = "text"
}: TaskMessageProps) {
  const [task, setTask] = useState<A2ATaskDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const getLatestArtifact = (task: A2ATaskDetailResponse): string => {
    if (task.task?.artifacts && task.task.artifacts.length > 0) {
      const latestArtifact =
        task.task.artifacts[task.task.artifacts.length - 1];
      if (latestArtifact.parts && latestArtifact.parts.length > 0) {
        return latestArtifact.parts[0].text || "";
      }
    }
    return "";
  };

  const getLatestHistory = (task: A2ATaskDetailResponse): string => {
    if (task.task?.history && task.task.history.length > 0) {
      const latestMessage = task.task.history[task.task.history.length - 1];
      if (latestMessage.parts && latestMessage.parts.length > 0) {
        return latestMessage.parts[0].text || "";
      }
    }
    return "";
  };

  const content = task
    ? getLatestArtifact(task) || getLatestHistory(task) || "Task in progress..."
    : "Loading task...";
  const markdownContent = useMarkdownProcessor(content);

  const getStatusIcon = () => {
    if (loading || !task) return <Clock className="h-4 w-4 animate-spin" />;

    switch (task.phase) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "running":
        return <Clock className="h-4 w-4 animate-pulse text-blue-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    if (loading || !task) return "bg-muted";

    switch (task.phase) {
      case "completed":
        return "bg-green-50 border-l-4 border-l-green-500";
      case "failed":
        return "bg-red-50 border-l-4 border-l-red-500";
      case "running":
        return "bg-blue-50 border-l-4 border-l-blue-500";
      default:
        return "bg-muted";
    }
  };

  const fetchTask = useCallback(async () => {
    try {
      const taskData = await a2aTaskService.getTaskByTaskId(namespace, taskId);
      if (taskData) {
        setTask(taskData);
        setError(null);

        // Stop polling if task is in terminal state
        if (
          taskData.phase === "completed" ||
          taskData.phase === "failed" ||
          taskData.phase === "cancelled"
        ) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } else {
        setError("Task not found");
      }
    } catch (err) {
      console.error("Error fetching task:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch task");
    } finally {
      setLoading(false);
    }
  }, [namespace, taskId]);

  useEffect(() => {
    fetchTask();

    // Start polling every 2 seconds
    intervalRef.current = setInterval(fetchTask, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [taskId, namespace, fetchTask]);

  if (error) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] rounded-lg px-3 py-2 bg-destructive/10 text-destructive">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm">Error loading task: {error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className={`max-w-[80%] rounded-lg px-3 py-2 ${getStatusColor()}`}>
        <div className="flex items-start gap-2">
          <div className="flex-shrink-0 mt-1">{getStatusIcon()}</div>
          <div className="flex-1">
            <div className="w-full flex flex-row items-center">
              <div className="text-xs text-muted-foreground mb-1">
                Task {task?.phase || "loading"}
                {task?.progress && ` • ${Math.round(task.progress * 100)}%`}
              </div>
              {task?.phase !== "completed" && (
                <div>
                  <TypingLoader
                    className=" w-[80px] scale-[0.75]"
                    transparent={true}
                  />
                </div>
              )}
            </div>
            {viewMode === "markdown" ? (
              <div className="text-sm">{markdownContent}</div>
            ) : (
              <pre className="text-sm whitespace-pre-wrap font-mono bg-transparent p-0 m-0 border-0">
                {content}
              </pre>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
