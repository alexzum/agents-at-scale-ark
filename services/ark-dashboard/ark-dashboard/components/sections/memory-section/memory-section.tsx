"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuItem
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from "@/components/ui/tooltip";
import type { MemoryFilters } from "@/lib/services/memory";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState, useMemo } from "react";

import { Database, MessageSquare, ChevronDown } from "lucide-react";
import { DeleteMemoryDropdownMenu } from "./delete-memory";
import { useGetAllMemoryMessages, useGetMemoryResources, useGetSessions } from "@/lib/services/memory-hooks";
import { cn } from "@/lib/utils";

export function MemorySection() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [memoryFilter, setMemoryFilter] = useState("");
  const [sessionFilter, setSessionFilter] = useState("");
  const [queryFilter, setQueryFilter] = useState("");

  const filters = {
    page: parseInt(searchParams.get("page") || "1", 10),
    limit: parseInt(searchParams.get("limit") || "10", 10),
    memoryName: searchParams.get("memory") || undefined,
    sessionId: searchParams.get("sessionId") || undefined,
    queryId: searchParams.get("queryId") || undefined
  }

  const memoryResources = useGetMemoryResources()
  const sessions = useGetSessions()
  const memoryMessages = useGetAllMemoryMessages({
    memory: filters.memoryName && filters.memoryName !== "all" ? filters.memoryName : undefined,
    session: filters.sessionId && filters.sessionId !== "all" ? filters.sessionId : undefined,
    query: filters.queryId && filters.queryId !== "all" ? filters.queryId : undefined
  })

  const filteredMemories = useMemo(() => {
    return memoryResources.data?.filter(memory =>
      memory.name.toLowerCase().includes(memoryFilter.toLowerCase())
    ) || [];
  }, [memoryResources.data, memoryFilter]);

  const filteredSessions = useMemo(() => {
    return Array.from(
      // Extract unique session IDs for filtering
      new Set(sessions.data?.map(s => s.sessionId))
    ).sort().filter(session =>
      session.toLowerCase().includes(sessionFilter.toLowerCase())
    )
  }, [sessions, sessionFilter])

  const sortedMessages = useMemo(() => {
    // Sort by sequence number descending (newest first) to maintain proper chronological order
    // This ensures messages appear in the correct order regardless of timestamp precision
    return memoryMessages.data?.sort((a, b) =>
      (b.sequence || 0) - (a.sequence || 0)
    ) || []
  }, [memoryMessages])

  const totalMessages = useMemo(() => {
    return sortedMessages.length
  }, [sortedMessages])

  const availableQueries = useMemo(() => {
    // Extract unique queryID - sessionID pairs
    return Array.from(
      new Map(
        sortedMessages?.map(m => [`${m.sessionId}-${m.queryId}`, {
          queryId: m.queryId,
          sessionId: m.sessionId
        }])
      ).values()
    ).sort(
      (a, b) => a.queryId.localeCompare(b.queryId)
    )
  }, [sortedMessages])

  const filteredQueries = useMemo(() => {
    return availableQueries.filter(query =>
      query.queryId.toLowerCase().includes(queryFilter.toLowerCase())
    );
  }, [availableQueries, queryFilter]);

  const totalPages = Math.max(1, Math.ceil(totalMessages / filters.limit));

  // Apply client-side pagination to the sorted messages
  const startIndex = (filters.page - 1) * filters.limit;
  const paginatedMessages = sortedMessages.slice(startIndex, startIndex + filters.limit);

  const updateUrlParams = useCallback(
    (params: Record<string, string | number | undefined>) => {
      const newParams = new URLSearchParams(searchParams.toString());

      Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") {
          newParams.delete(key);
        } else {
          newParams.set(key, String(value));
        }
      });

      const newUrl =
        pathname + (newParams.toString() ? `?${newParams.toString()}` : "");
      router.push(newUrl, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  const handleFilterChange = (
    key: keyof MemoryFilters,
    value: string | undefined
  ) => {
    const effectiveValue = value === "all" ? undefined : value;
    updateUrlParams({
      [key]: effectiveValue,
      page: 1
    });
  };

  const clearFilters = () => {
    updateUrlParams({
      page: 1,
      limit: filters.limit,
      memoryName: undefined,
      sessionId: undefined,
      queryId: undefined
    });
  };

  const handlePageChange = (newPage: number) => {
    updateUrlParams({ page: newPage });
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    } catch {
      return timestamp;
    }
  };

  const handleItemsPerPageChange = (newLimit: number) => {
    // Only update URL - let the useEffect handle state updates
    updateUrlParams({
      limit: newLimit,
      page: 1
    });
  };

  if (memoryResources.isPending || sessions.isPending || memoryMessages.isPending) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Database className="h-8 w-8 animate-pulse mx-auto mb-4 text-gray-400" />
          <p className="text-gray-500">Loading memory messages...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap gap-4 items-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-48 justify-between text-sm h-9 font-normal min-w-0">
              <span className={cn('truncate min-w-0', {
                'text-muted-foreground': !searchParams.get("memory") || searchParams.get("memory") === "all"
              })}>
                {!searchParams.get("memory") || searchParams.get("memory") === "all"
                  ? "All Memories"
                  : filters.memoryName
                }
              </span>
              <ChevronDown className="h-4 w-4 flex-shrink-0 ml-1" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-48" align="start">
            <div className="p-2">
              <Input
                autoFocus
                placeholder="Filter memories..."
                value={memoryFilter}
                onChange={(e) => setMemoryFilter(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <DropdownMenuSeparator />
            <div className="max-h-64 overflow-auto">
              <DropdownMenuItem onClick={() => {
                updateUrlParams({ memory: undefined, page: 1 });
              }}>
                All Memories
              </DropdownMenuItem>
              {filteredMemories.map((memory) => (
                <DropdownMenuItem
                  key={memory.name}
                  onClick={() => {
                    updateUrlParams({ memory: memory.name, page: 1 });
                  }}
                >
                  {memory.name}
                </DropdownMenuItem>
              ))}
              {filteredMemories.length === 0 && memoryFilter && (
                <div className="p-3 text-sm text-gray-500">
                  No memories match your filter
                </div>
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-64 justify-between text-sm h-9 font-normal min-w-0">
              <span className={cn('truncate min-w-0', {
                'text-muted-foreground': !searchParams.get("sessionId") || searchParams.get("sessionId") === "all"
              })}>
                {!searchParams.get("sessionId") || searchParams.get("sessionId") === "all"
                  ? "All Sessions"
                  : filters.sessionId
                }
              </span>
              <ChevronDown className="h-4 w-4 flex-shrink-0 ml-1" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-64" align="start">
            <div className="p-2">
              <Input
                autoFocus
                placeholder="Filter sessions..."
                value={sessionFilter}
                onChange={(e) => setSessionFilter(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <DropdownMenuSeparator />
            <div className="max-h-64 overflow-auto">
              <DropdownMenuItem
                onClick={() => {
                  handleFilterChange("sessionId", "all")
                }}
              >
                All Sessions
              </DropdownMenuItem>
              {filteredSessions.map((sessionId) => (
                <DropdownMenuItem
                  key={sessionId}
                  onClick={() => {
                    handleFilterChange("sessionId", sessionId);
                  }}
                >
                  {sessionId.length > 30 ? `${sessionId.substring(0, 30)}...` : sessionId}
                </DropdownMenuItem>
              ))}
              {filteredSessions.length === 0 && sessionFilter && (
                <div className="p-3 text-sm text-gray-500">
                  No sessions match your filter
                </div>
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-64 justify-between text-sm h-9 font-normal min-w-0">
              <span className={cn('truncate min-w-0', {
                'text-muted-foreground': !searchParams.get("queryId") || searchParams.get("queryId") === "all"
              })}>
                {!searchParams.get("queryId") || searchParams.get("queryId") === "all"
                  ? "All Queries"
                  : filters.queryId
                }
              </span>
              <ChevronDown className="h-4 w-4 flex-shrink-0 ml-1" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-64" align="start">
            <div className="p-2">
              <Input
                autoFocus
                placeholder="Filter queries..."
                value={queryFilter}
                onChange={(e) => setQueryFilter(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <DropdownMenuSeparator />
            <div className="max-h-64 overflow-auto">
              <DropdownMenuItem
                onClick={() => {
                  handleFilterChange("queryId", "all");
                }}
              >
                All Queries
              </DropdownMenuItem>
              {filteredQueries.map(({ queryId }) => (
                <DropdownMenuItem
                  key={queryId}
                  onClick={() => {
                    handleFilterChange("queryId", queryId);
                  }}
                >
                  {queryId.length > 30 ? `${queryId.substring(0, 30)}...` : queryId}
                </DropdownMenuItem>
              ))}
              {filteredQueries.length === 0 && queryFilter && (
                <div className="p-3 text-sm text-gray-500">
                  No queries match your filter
                </div>
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="outline"
          size="sm"
          onClick={clearFilters}
          disabled={
            !(
              (filters.memoryName && filters.memoryName !== "all") ||
              (filters.sessionId && filters.sessionId !== "all") ||
              (filters.queryId && filters.queryId !== "all")
            )
          }
        >
          Clear Filters
        </Button>
        <DeleteMemoryDropdownMenu
          className="ml-auto"
          selectedQuery={
            searchParams.get("queryId") ? filteredQueries.find(
              q => q.queryId === searchParams.get("queryId")
            ) : undefined
          }
          selectedSession={searchParams.get("sessionId")}
          onSuccess={clearFilters}
        />
      </div>

      {/* Messages Table */}
      <div className="border rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Memory
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Session
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Query
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Message
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
              {paginatedMessages.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-3 py-8 text-center text-xs text-gray-500 dark:text-gray-400"
                  >
                    <div className="flex flex-col items-center">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p>No messages found</p>
                      {totalMessages > 0 && (
                        <p className="mt-1 text-xs text-gray-400">
                          Try adjusting your filters or page selection
                        </p>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedMessages.map((messageRecord, index) => (
                  <tr
                    key={`${messageRecord.sessionId}-${messageRecord.queryId}-${index}`}
                    className="hover:bg-gray-50 dark:hover:bg-gray-900/30 transition-colors"
                  >
                    <td className="px-3 py-3 text-xs font-mono text-gray-600 dark:text-gray-300">
                      {formatTimestamp(messageRecord.timestamp)}
                    </td>
                    <td className="px-3 py-3 text-xs font-mono">
                      <div className="truncate max-w-20">
                        {messageRecord.memoryName}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-xs font-mono">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger className="text-left">
                            <div className="truncate max-w-24">
                              {messageRecord.sessionId}
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="font-mono text-xs">{messageRecord.sessionId}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </td>
                    <td className="px-3 py-3 text-xs font-mono">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger className="text-left">
                            <div className="truncate max-w-24">
                              {messageRecord.queryId}
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="font-mono text-xs">{messageRecord.queryId}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </td>
                    <td className="px-3 py-3 text-xs font-mono">
                      <pre className="text-xs text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                        {JSON.stringify(messageRecord.message, null, 2)}
                      </pre>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary and Pagination */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Showing {paginatedMessages.length > 0 ? startIndex + 1 : 0} to {Math.min(startIndex + filters.limit, totalMessages)} of {totalMessages} messages
        </div>
        <Pagination
          currentPage={filters.page}
          totalPages={totalPages}
          itemsPerPage={filters.limit}
          onPageChange={handlePageChange}
          onItemsPerPageChange={handleItemsPerPageChange}
        />
      </div>
    </div>
  );
}