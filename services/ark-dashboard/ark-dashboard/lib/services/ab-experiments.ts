import { apiClient } from "@/lib/api/client";
import type { ABExperiment, ABExperimentModifications } from "@/lib/types/ab-experiment";
import type { components } from "@/lib/api/generated/types";

type QueryDetailResponse = components["schemas"]["QueryDetailResponse"];
type AgentDetailResponse = components["schemas"]["AgentDetailResponse"];

export interface CreateABExperimentRequest {
  modifications: ABExperimentModifications
  createdBy?: string
}

export interface UpdateABExperimentRequest {
  status?: ABExperiment['status']
  results?: ABExperiment['results']
}

export interface ApplyWinnerRequest {
  winner: 'baseline' | 'experiment'
}

export const abExperimentsService = {
  async create(
    namespace: string,
    queryName: string,
    request: CreateABExperimentRequest
  ): Promise<ABExperiment> {
    const response = await apiClient.post<ABExperiment>(
      `/api/v1/namespaces/${namespace}/queries/${queryName}/ab-experiment`,
      request
    );
    return response;
  },

  async get(
    namespace: string,
    queryName: string,
    experimentId: string
  ): Promise<ABExperiment> {
    const response = await apiClient.get<ABExperiment>(
      `/api/v1/namespaces/${namespace}/queries/${queryName}/ab-experiment/${experimentId}`
    );
    return response;
  },

  async update(
    namespace: string,
    queryName: string,
    experimentId: string,
    request: UpdateABExperimentRequest
  ): Promise<ABExperiment> {
    const response = await apiClient.patch<ABExperiment>(
      `/api/v1/namespaces/${namespace}/queries/${queryName}/ab-experiment/${experimentId}`,
      request
    );
    return response;
  },

  async applyWinner(
    namespace: string,
    queryName: string,
    experimentId: string,
    request: ApplyWinnerRequest
  ): Promise<QueryDetailResponse> {
    const response = await apiClient.post<QueryDetailResponse>(
      `/api/v1/namespaces/${namespace}/queries/${queryName}/ab-experiment/${experimentId}/apply`,
      request
    );
    return response;
  },

  async delete(
    namespace: string,
    queryName: string,
    experimentId: string
  ): Promise<void> {
    await apiClient.delete(
      `/api/v1/namespaces/${namespace}/queries/${queryName}/ab-experiment/${experimentId}`
    );
  },

  async streamExperimentStatus(
    namespace: string,
    queryName: string,
    experimentId: string,
    onUpdate: (experiment: ABExperiment) => void
  ): Promise<{ terminal: boolean; finalStatus: ABExperiment['status'] }> {
    return new Promise((resolve) => {
      const pollStatus = async () => {
        try {
          const experiment = await this.get(namespace, queryName, experimentId);

          onUpdate(experiment);

          if (
            experiment.status === "completed" ||
            experiment.status === "failed"
          ) {
            resolve({ terminal: true, finalStatus: experiment.status });
          } else {
            setTimeout(pollStatus, 2000);
          }
        } catch (error) {
          console.error(
            `Error streaming status for experiment ${experimentId}:`,
            error
          );
          resolve({ terminal: true, finalStatus: "failed" });
        }
      };

      pollStatus();
    });
  },

  async getTargetAgent(
    namespace: string,
    agentName: string
  ): Promise<AgentDetailResponse> {
    const response = await apiClient.get<AgentDetailResponse>(
      `/api/v1/namespaces/${namespace}/agents/${agentName}`
    );
    return response;
  }
};
