import { useQuery } from "@tanstack/react-query";
import { agentsService } from "./agents";

export const GET_ALL_AGENTS_QUERY_KEY = "get-all-agents";
export const GET_AGENT_QUERY_KEY = "get-agent";

export const useGetAllAgents = () => {
  return useQuery({
    queryKey: [GET_ALL_AGENTS_QUERY_KEY],
    queryFn: agentsService.getAll
  });
};

export const useGetAgent = (name: string | undefined) => {
  return useQuery({
    queryKey: [GET_AGENT_QUERY_KEY, name],
    queryFn: () => name ? agentsService.getByName(name) : null,
    enabled: !!name
  });
};
