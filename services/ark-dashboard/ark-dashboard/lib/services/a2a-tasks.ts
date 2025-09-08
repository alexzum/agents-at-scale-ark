import { apiClient } from "@/lib/api/client";

// Manually define A2ATask types until they are properly generated
export interface A2ATaskPart {
  kind: "text" | "file" | "data";
  text?: string;
  data?: string;
  uri?: string;
  mime_type?: string;
  metadata?: Record<string, string>;
}

export interface A2ATaskArtifact {
  artifact_id: string;
  name?: string;
  description?: string;
  parts: A2ATaskPart[];
  metadata?: Record<string, string>;
}

export interface A2ATaskMessage {
  role: "user" | "agent" | "system";
  parts: A2ATaskPart[];
  metadata?: Record<string, string>;
}

export interface A2ATaskStatus {
  state: "submitted" | "working" | "input-required" | "completed" | "canceled" | "failed" | "rejected" | "auth-required" | "unknown";
  message?: A2ATaskMessage;
  timestamp?: string;
}

export interface A2ATaskTask {
  id: string;
  session_id?: string;
  status: A2ATaskStatus;
  artifacts?: A2ATaskArtifact[];
  history?: A2ATaskMessage[];
  metadata?: Record<string, string>;
}

export interface A2ATaskQueryRef {
  name: string;
  namespace: string;
}

export interface A2ATaskAssignedAgent {
  name: string;
  namespace: string;
}

export interface A2ATaskResponse {
  name: string;
  namespace: string;
  task_id: string;
  phase: "pending" | "assigned" | "running" | "completed" | "failed" | "cancelled";
  priority: number;
  timeout?: string;
  query_ref?: A2ATaskQueryRef;
  assigned_agent?: A2ATaskAssignedAgent;
  start_time?: string;
  completion_time?: string;
  creation_timestamp?: string;
  progress?: number;
}

export interface A2ATaskDetailResponse extends A2ATaskResponse {
  task?: A2ATaskTask;
}

export interface A2ATaskListResponse {
  items: A2ATaskResponse[];
  total: number;
}

interface AxiosError extends Error {
  response?: {
    status: number;
  };
}

export const a2aTaskService = {
  async getTask(
    namespace: string,
    taskName: string
  ): Promise<A2ATaskDetailResponse | null> {
    try {
      return await apiClient.get<A2ATaskDetailResponse>(
        `/api/v1/namespaces/${namespace}/a2atasks/${taskName}`
      );
    } catch (error) {
      if ((error as AxiosError).response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  async getTaskByTaskId(
    namespace: string,
    taskId: string
  ): Promise<A2ATaskDetailResponse | null> {
    try {
      // First, list tasks filtered by taskId
      const params = new URLSearchParams();
      params.append("taskId", taskId);
      
      const listResult = await apiClient.get<A2ATaskListResponse>(
        `/api/v1/namespaces/${namespace}/a2atasks?${params.toString()}`
      );
      
      if (listResult.items.length === 0) {
        return null;
      }
      
      // Get the first matching task by name
      const taskName = listResult.items[0].name;
      return await this.getTask(namespace, taskName);
    } catch (error) {
      if ((error as AxiosError).response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  async listTasks(
    namespace: string,
    phase?: string,
    agentName?: string
  ): Promise<A2ATaskListResponse> {
    const params = new URLSearchParams();
    if (phase) params.append("phase", phase);
    if (agentName) params.append("agent_name", agentName);
    
    const query = params.toString() ? `?${params.toString()}` : "";
    
    return await apiClient.get<A2ATaskListResponse>(
      `/api/v1/namespaces/${namespace}/a2atasks/${query}`
    );
  }
};