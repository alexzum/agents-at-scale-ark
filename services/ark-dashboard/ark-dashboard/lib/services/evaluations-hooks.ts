import { useQuery } from "@tanstack/react-query";
import { evaluationsService } from "./evaluations";

type Props = {
  enhanced?: boolean;
}

export const useGetAllEvaluationsWithDetails = ({ enhanced = false }: Props) => {
  return useQuery({
    queryKey: ["get-all-evaluations-with-details", enhanced],
    queryFn: async () => {
      try {
        // Try enhanced fetch first
        return await evaluationsService.getAllWithDetails(enhanced);
      } catch {
        // Fallback to basic fetch
        return await evaluationsService.getAll();
      }
    }
  });
};

type GetEvaluationsProps = {
  namespace?: string;
  labelSelector?: string;
  queryRef?: string;
}

export const useGetEvaluations = ({ namespace, labelSelector, queryRef }: GetEvaluationsProps) => {
  return useQuery({
    queryKey: ["get-evaluations", namespace, labelSelector, queryRef],
    queryFn: async () => {
      return await evaluationsService.getAll(namespace, labelSelector, queryRef);
    },
    refetchInterval: false,
    enabled: !!namespace || !!labelSelector || !!queryRef
  });
};
