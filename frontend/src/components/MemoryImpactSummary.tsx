import { useMemo } from "react";

import type {
  MemoryMetrics,
} from "../hooks/useMemoryMetrics";

import type {
  RelayMemory,
} from "../types/api";

interface MemoryImpactSummaryProps {
  memories: RelayMemory[];
  metricsByMemoryId: Record<string, MemoryMetrics>;
  isLoading: boolean;
}

function formatPercentage(value: number | null): string {
  if (value === null) {
    return "Not scored";
  }

  return `${Math.round(value * 100)}%`;
}

export default function MemoryImpactSummary({
  memories,
  metricsByMemoryId,
  isLoading,
}: MemoryImpactSummaryProps) {
  const summary = useMemo(() => {
    const metrics = Object.values(metricsByMemoryId);

    const totalAcceptedReuses = metrics.reduce(
      (total, item) =>
        total + item.acceptedReuseCount,
      0,
    );

    const totalTimeSavedMinutes = metrics.reduce(
      (total, item) =>
        total + item.totalTimeSavedMinutes,
      0,
    );

    const totalStepsSkipped = metrics.reduce(
      (total, item) =>
        total + item.totalStepsSkipped,
      0,
    );

    const similarityScores = metrics
      .map((item) => item.averageSimilarity)
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

    const reusedMemoryCount = metrics.filter(
      (item) => item.acceptedReuseCount > 0,
    ).length;

    return {
      totalAcceptedReuses,
      totalTimeSavedMinutes,
      totalStepsSkipped,
      averageSimilarity,
      reusedMemoryCount,
    };
  }, [metricsByMemoryId]);

  const reuseRate =
    memories.length > 0
      ? summary.reusedMemoryCount / memories.length
      : 0;

  return (
    <section className="relay-impact-panel">
      <header className="relay-impact-panel-header">
        <div>
          <p className="relay-eyebrow">
            Compounding organizational knowledge
          </p>

          <h2>Memory impact</h2>

          <p>
            Relay tracks how verified resolutions accelerate
            later investigations.
          </p>
        </div>

        <span className="relay-impact-status">
          {isLoading
            ? "Calculating impact…"
            : `${summary.totalAcceptedReuses} accepted ${
                summary.totalAcceptedReuses === 1
                  ? "reuse"
                  : "reuses"
              }`}
        </span>
      </header>

      <div className="relay-impact-grid">
        <article>
          <span>Accepted memory reuses</span>

          <strong>
            {isLoading
              ? "…"
              : summary.totalAcceptedReuses}
          </strong>

          <small>
            Verified precedents used by later agents
          </small>
        </article>

        <article>
          <span>Estimated time saved</span>

          <strong>
            {isLoading
              ? "…"
              : `${summary.totalTimeSavedMinutes} min`}
          </strong>

          <small>
            Investigation effort avoided through reuse
          </small>
        </article>

        <article>
          <span>Steps skipped</span>

          <strong>
            {isLoading
              ? "…"
              : summary.totalStepsSkipped}
          </strong>

          <small>
            Repeated investigation steps eliminated
          </small>
        </article>

        <article>
          <span>Average similarity</span>

          <strong>
            {isLoading
              ? "…"
              : formatPercentage(
                  summary.averageSimilarity,
                )}
          </strong>

          <small>
            Relevance of accepted inherited memories
          </small>
        </article>
      </div>

      <footer className="relay-impact-footer">
        <div>
          <span>Memories reused</span>

          <strong>
            {summary.reusedMemoryCount} of {memories.length}
          </strong>
        </div>

        <div className="relay-impact-progress">
          <span
            style={{
              width: `${Math.min(
                Math.max(reuseRate * 100, 0),
                100,
              )}%`,
            }}
          />
        </div>

        <small>
          {memories.length === 0
            ? "Archive an approved investigation to create the first verified memory."
            : summary.reusedMemoryCount === 0
              ? "Verified memories are ready for future investigations."
              : "Relay is successfully compounding knowledge across investigations."}
        </small>
      </footer>
    </section>
  );
}