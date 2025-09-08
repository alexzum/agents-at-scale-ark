import { apiClient } from "@/lib/api/client";
import type { components } from "@/lib/api/generated/types";

export type A2ATaskDetailResponse = components["schemas"]["A2ATaskDetailResponse"];
export type A2ATaskListResponse = components["schemas"]["A2ATaskListResponse"];

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