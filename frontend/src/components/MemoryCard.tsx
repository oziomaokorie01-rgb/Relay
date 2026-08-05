import type {
  MemoryMetrics,
} from "../hooks/useMemoryMetrics";

import type {
  RelayMemory,
} from "../types/api";

interface MemoryCardProps {
  memory: RelayMemory;
  metrics?: MemoryMetrics;
  isLoadingMetrics?: boolean;
  onOpen: (memoryId: string) => void;
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function MemoryCard({
  memory,
  metrics,
  isLoadingMetrics = false,
  onOpen,
}: MemoryCardProps) {
  const acceptedReuseCount =
    metrics?.acceptedReuseCount ?? 0;

  const totalTimeSaved =
    metrics?.totalTimeSavedMinutes ?? 0;

  const totalStepsSkipped =
    metrics?.totalStepsSkipped ?? 0;

  return (
    <article className="relay-memory-card">
      <div className="relay-memory-card-header">
        <span className="relay-status-badge is-verified">
          ✓ Verified
        </span>

        <span>Version {memory.version}</span>
      </div>

      <div className="relay-memory-card-body">
        <div className="relay-memory-card-copy">
          <h3>{memory.title}</h3>
          <p>{memory.summary}</p>
        </div>

        <div className="relay-memory-card-impact">
          <article>
            <span>Confidence</span>
            <strong>
              {formatConfidence(memory.confidence)}
            </strong>
          </article>

          <article>
            <span>Reuses</span>
            <strong>
              {isLoadingMetrics
                ? "…"
                : acceptedReuseCount}
            </strong>
          </article>

          <article>
            <span>Time saved</span>
            <strong>
              {isLoadingMetrics
                ? "…"
                : `${totalTimeSaved}m`}
            </strong>
          </article>
        </div>
      </div>

      <dl className="relay-memory-card-details">
        <div>
          <dt>Incident</dt>
          <dd>{formatLabel(memory.incident_type)}</dd>
        </div>

        <div>
          <dt>Primary asset</dt>
          <dd title={memory.primary_asset_urn}>
            {memory.primary_asset_urn}
          </dd>
        </div>

        <div>
          <dt>Steps skipped</dt>
          <dd>
            {isLoadingMetrics
              ? "Loading"
              : totalStepsSkipped}
          </dd>
        </div>
      </dl>

      <div className="relay-memory-card-keywords">
        <span className="relay-memory-card-section-label">
          Retrieval keywords
        </span>

        <div className="relay-keyword-list">
          {memory.keywords
            .slice(0, 5)
            .map((keyword) => (
              <span key={keyword}>
                {keyword}
              </span>
            ))}
        </div>
      </div>

      <div className="relay-memory-card-action">
        <button
          className="relay-secondary-button relay-memory-open-button"
          type="button"
          onClick={() => onOpen(memory.id)}
        >
          Open memory
        </button>
      </div>
    </article>
  );
}