import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ApiError,
  getMemoryReuseHistory,
} from "../lib/api";

import type {
  MemoryReuseEvent,
  RelayMemory,
} from "../types/api";

export interface MemoryMetrics {
  memoryId: string;
  reuseCount: number;
  acceptedReuseCount: number;
  totalTimeSavedMinutes: number;
  totalStepsSkipped: number;
  averageSimilarity: number | null;
  reuseEvents: MemoryReuseEvent[];
}

interface UseMemoryMetricsResult {
  metricsByMemoryId: Record<string, MemoryMetrics>;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Could not load memory reuse metrics.";
}

function calculateMetrics(
  memoryId: string,
  events: MemoryReuseEvent[],
): MemoryMetrics {
  const acceptedEvents = events.filter(
    (event) => event.accepted,
  );

  const similarityScores = acceptedEvents
    .map((event) => event.similarity_score)
    .filter(
      (score): score is number =>
        typeof score === "number",
    );

  const averageSimilarity =
    similarityScores.length > 0
      ? similarityScores.reduce(
          (total, score) => total + score,
          0,
        ) / similarityScores.length
      : null;

  return {
    memoryId,
    reuseCount: events.length,
    acceptedReuseCount: acceptedEvents.length,
    totalTimeSavedMinutes: acceptedEvents.reduce(
      (total, event) =>
        total +
        event.estimated_time_saved_minutes,
      0,
    ),
    totalStepsSkipped: acceptedEvents.reduce(
      (total, event) =>
        total + event.estimated_steps_skipped,
      0,
    ),
    averageSimilarity,
    reuseEvents: events,
  };
}

export default function useMemoryMetrics(
  memories: RelayMemory[],
): UseMemoryMetricsResult {
  const [metricsByMemoryId, setMetricsByMemoryId] =
    useState<Record<string, MemoryMetrics>>({});

  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState<string | null>(
    null,
  );

  const memoryIds = useMemo(
    () => memories.map((memory) => memory.id),
    [memories],
  );

  const memoryIdsKey = useMemo(
    () => memoryIds.join("|"),
    [memoryIds],
  );

  const loadMetrics = useCallback(async () => {
    if (memoryIds.length === 0) {
      setMetricsByMemoryId({});
      setError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled(
        memoryIds.map(async (memoryId) => {
          const events =
            await getMemoryReuseHistory(memoryId);

          return calculateMetrics(
            memoryId,
            events,
          );
        }),
      );

      const nextMetrics: Record<
        string,
        MemoryMetrics
      > = {};

      const failedMessages: string[] = [];

      results.forEach((result, index) => {
        const memoryId = memoryIds[index];

        if (result.status === "fulfilled") {
          nextMetrics[memoryId] = result.value;
          return;
        }

        failedMessages.push(
          getErrorMessage(result.reason),
        );

        nextMetrics[memoryId] = calculateMetrics(
          memoryId,
          [],
        );
      });

      setMetricsByMemoryId(nextMetrics);

      if (failedMessages.length > 0) {
        setError(
          "Some memory reuse metrics could not be loaded.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, [memoryIdsKey]);

  useEffect(() => {
    void loadMetrics();
  }, [loadMetrics]);

  return {
    metricsByMemoryId,
    isLoading,
    error,
    refresh: loadMetrics,
  };
}