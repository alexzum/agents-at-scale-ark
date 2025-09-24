'use client';

import { toast } from '@/components/ui/use-toast';
import { Namespace } from '@/lib/services';
import { useCreateNamespace, useGetContext, useGetAllNamespaces } from '@/lib/services/namespaces-hooks';
import { usePathname, useSearchParams, useRouter } from 'next/navigation';
import type { PropsWithChildren } from 'react';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react';

interface NamespaceContext {
  availableNamespaces: Namespace[];
  createNamespace: (name: string) => void;
  isPending: boolean;
  namespace: string;
  namespaceResolved: boolean;
  setNamespace: (namespace: string) => void;
}

const NamespaceContext = createContext<NamespaceContext | undefined>(
  undefined
);

const NamespaceProvider = ({ children }: PropsWithChildren) => {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const namespaceFromQueryParams = searchParams.get('namespace') || "default";
  const [namespaceResolved, setNamespaceResolved] = useState(false);

  const {
    data,
    isPending,
    error
  } = useGetContext()

  const {
    data: availableNamespaces = [],
    isPending: namespacesLoading
  } = useGetAllNamespaces()
  
  const createQueryString = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams()
      params.set(name, value)
      
      return params.toString()
    },
    []
  )
  
  const setNamespace = useCallback((namespace: string) => {
    const newQueryParams = createQueryString('namespace', namespace)
    router.push(pathname + '?' + newQueryParams)
  }, [pathname, router, createQueryString])

  const { mutate } = useCreateNamespace({
    onSuccess: setNamespace
  })

  const createNamespace = useCallback((name: string) => {
    mutate(name)
  }, [mutate])

  useEffect(() => {
    if(error) {
      toast({
        variant: "destructive",
        title: `Failed to get namespace`,
        description:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred"
      })
    }
  }, [error])

  useEffect(() => {
    // Mark namespace as resolved once we have context data
    // Don't override user's namespace selection with context
    if(data) {
      setNamespaceResolved(true)
    }
  }, [data])

  const context = useMemo<NamespaceContext>(() => ({
    availableNamespaces,
    createNamespace,
    isPending: isPending || namespacesLoading,
    namespace: namespaceFromQueryParams,
    namespaceResolved,
    setNamespace
  }),[
    availableNamespaces,
    createNamespace,
    isPending,
    namespacesLoading,
    namespaceFromQueryParams,
    namespaceResolved,
    setNamespace
  ]);

  return (
    <NamespaceContext.Provider value={context}>
      {children}
    </NamespaceContext.Provider>
  );
};

const useNamespace = () => {
  const context = useContext(NamespaceContext);
  if (!context) {
    throw new Error('useNamespace must be used within a NamespaceProvider');
  }

  return context;
};

export { NamespaceProvider, useNamespace };
