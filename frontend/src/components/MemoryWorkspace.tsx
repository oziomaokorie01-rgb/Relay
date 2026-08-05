import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ApiError,
  getMemory,
  getMemoryReuseHistory,
} from "../lib/api";

import type {
  MemoryReuseEvent,
  RelayMemory,
} from "../types/api";
import CopyButton from "./CopyButton";
import ExportMemoryButton from "./ExportMemoryButton";
import ShareMemoryButton from "./ShareMemoryButton";

interface MemoryWorkspaceProps {
  memoryId: string;
  onClose: () => void;
  onOpenInvestigation?: (investigationId: string) => void;
}

interface MemoryWorkspaceData {
  memory: RelayMemory | null;
  reuseEvents: MemoryReuseEvent[];
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred.";
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string | null): string {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatConfidence(value: number | null): string {
  if (value === null) {
    return "Not scored";
  }

  return `${Math.round(value * 100)}%`;
}

function truncateId(value: string): string {
  if (value.length <= 18) {
    return value;
  }

  return `${value.slice(0, 8)}…${value.slice(-6)}`;
}

export default function MemoryWorkspace({
  memoryId,
  onClose,
  onOpenInvestigation,
}: MemoryWorkspaceProps) {
  const [data, setData] = useState<MemoryWorkspaceData>({
    memory: null,
    reuseEvents: [],
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMemory = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [memory, reuseEvents] = await Promise.all([
        getMemory(memoryId),
        getMemoryReuseHistory(memoryId),
      ]);

      setData({
        memory,
        reuseEvents,
      });
    } catch (loadError) {
      setError(getErrorMessage(loadError));
    } finally {
      setIsLoading(false);
    }
  }, [memoryId]);

  useEffect(() => {
    void loadMemory();
  }, [loadMemory]);

  const memory = data.memory;

  const totalTimeSaved = useMemo(
    () =>
      data.reuseEvents.reduce(
        (total, event) =>
          total + event.estimated_time_saved_minutes,
        0,
      ),
    [data.reuseEvents],
  );

  const totalStepsSkipped = useMemo(
    () =>
      data.reuseEvents.reduce(
        (total, event) =>
          total + event.estimated_steps_skipped,
        0,
      ),
    [data.reuseEvents],
  );

  const acceptedReuseCount = useMemo(
    () =>
      data.reuseEvents.filter((event) => event.accepted).length,
    [data.reuseEvents],
  );

  if (isLoading && !memory) {
    return (
      <section className="relay-memory-workspace">
        <div className="relay-workspace-loading">
          Loading verified memory…
        </div>
      </section>
    );
  }

  if (!memory) {
    return (
      <section className="relay-memory-workspace">
        <button
          className="relay-back-button"
          type="button"
          onClick={onClose}
        >
          ← Back to Memory Library
        </button>

        <div className="relay-alert relay-alert-error">
          <strong>Relay could not load this memory.</strong>
          <span>
            {error ?? "The requested memory was not found."}
          </span>
        </div>
      </section>
    );
  }

  return (
    <section className="relay-memory-workspace">
      <header className="relay-memory-workspace-header">
        <div>
          <button
            className="relay-back-button"
            type="button"
            onClick={onClose}
          >
            ← Back to Memory Library
          </button>

          <div className="relay-memory-title-row">
            <div>
              <p className="relay-eyebrow">
                Verified organizational memory
              </p>

              <h2>{memory.title}</h2>
            </div>

            <span
              className={`relay-status-badge is-${memory.verification_status}`}
            >
              {formatLabel(memory.verification_status)}
            </span>
          </div>

          <p className="relay-memory-workspace-summary">
            {memory.summary}
          </p>
        </div>

        <div className="relay-memory-header-actions">
  <ShareMemoryButton memory={memory} />

  <ExportMemoryButton
    memory={memory}
    reuseEvents={data.reuseEvents}
  />

  <button
    className="relay-refresh-button"
    type="button"
    disabled={isLoading}
    onClick={() => void loadMemory()}
  >
    {isLoading ? "Refreshing…" : "Refresh memory"}
  </button>
</div>
      </header>

      {error && (
        <div className="relay-alert relay-alert-error">
          <strong>Relay encountered a problem.</strong>
          <span>{error}</span>
        </div>
      )}

      <section className="relay-memory-summary-grid">
        <article>
          <span>Confidence</span>
          <strong>{formatConfidence(memory.confidence)}</strong>
        </article>

        <article>
          <span>Version</span>
          <strong>{memory.version}</strong>
        </article>

        <article>
          <span>Reuse events</span>
          <strong>{data.reuseEvents.length}</strong>
        </article>

        <article>
          <span>Accepted reuses</span>
          <strong>{acceptedReuseCount}</strong>
        </article>

        <article>
          <span>Time saved</span>
          <strong>{totalTimeSaved} min</strong>
        </article>

        <article>
          <span>Steps skipped</span>
          <strong>{totalStepsSkipped}</strong>
        </article>
      </section>

      <div className="relay-memory-workspace-grid">
        <div className="relay-memory-workspace-main">
          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Institutional knowledge
                </p>
                <h3>Root cause</h3>
              </div>
            </div>

            <p className="relay-memory-long-text">
              {memory.root_cause}
            </p>
          </article>

         <article className="relay-panel">
  <div className="relay-panel-heading">
    <div>
      <p className="relay-eyebrow">
        Verified remediation
      </p>

      <h3>Resolution</h3>
    </div>

    <CopyButton
      value={memory.resolution}
      idleLabel="Copy resolution"
      successLabel="Copied"
    />
  </div>

  <pre className="relay-memory-resolution">
    <code>{memory.resolution}</code>
  </pre>
</article>

          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Knowledge reuse
                </p>
                <h3>Reuse history</h3>
              </div>

              <span className="relay-count-badge">
                {data.reuseEvents.length}
              </span>
            </div>

            {data.reuseEvents.length === 0 ? (
              <div className="relay-empty-state">
                This verified memory has not been reused by another
                investigation yet.
              </div>
            ) : (
              <div className="relay-memory-reuse-list">
                {data.reuseEvents.map((event) => (
                  <article
                    className="relay-memory-reuse-card"
                    key={event.id}
                  >
                    <div className="relay-memory-reuse-card-header">
                      <div>
                        <span>
                          {formatLabel(event.reuse_type)}
                        </span>

                        <strong>
                          {formatConfidence(
                            event.similarity_score,
                          )}{" "}
                          similarity
                        </strong>
                      </div>

                      <span
                        className={
                          event.accepted
                            ? "relay-reuse-accepted"
                            : "relay-reuse-rejected"
                        }
                      >
                        {event.accepted
                          ? "Accepted"
                          : "Not accepted"}
                      </span>
                    </div>

                    <p>{event.agent_explanation}</p>

                    <dl>
                      <div>
                        <dt>Investigation</dt>
                        <dd title={event.investigation_id}>
                          {truncateId(event.investigation_id)}
                        </dd>
                      </div>

                      <div>
                        <dt>Steps skipped</dt>
                        <dd>
                          {event.estimated_steps_skipped}
                        </dd>
                      </div>

                      <div>
                        <dt>Time saved</dt>
                        <dd>
                          {
                            event.estimated_time_saved_minutes
                          }{" "}
                          min
                        </dd>
                      </div>

                      <div>
                        <dt>Reused</dt>
                        <dd>{formatDate(event.created_at)}</dd>
                      </div>
                    </dl>

                    {onOpenInvestigation && (
                      <button
                        className="relay-secondary-button"
                        type="button"
                        onClick={() =>
                          onOpenInvestigation(
                            event.investigation_id,
                          )
                        }
                      >
                        Open investigation
                      </button>
                    )}
                  </article>
                ))}
              </div>
            )}
          </article>
        </div>

        <aside className="relay-memory-workspace-sidebar">
          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Classification
                </p>
                <h3>Memory details</h3>
              </div>
            </div>

            <dl className="relay-definition-list">
              <div>
  <dt>Memory key</dt>

  <dd className="relay-copyable-value">
    <span>{memory.memory_key}</span>

    <CopyButton
      value={memory.memory_key}
      idleLabel="Copy"
      successLabel="Copied"
    />
  </dd>
</div>

              <div>
                <dt>Incident type</dt>
                <dd>{formatLabel(memory.incident_type)}</dd>
              </div>

              <div>
  <dt>Primary asset</dt>

  <dd className="relay-copyable-value">
    <span>{memory.primary_asset_urn}</span>

    <CopyButton
      value={memory.primary_asset_urn}
      idleLabel="Copy"
      successLabel="Copied"
    />
  </dd>
</div>

              <div>
                <dt>Created</dt>
                <dd>{formatDate(memory.created_at)}</dd>
              </div>

              <div>
                <dt>Verified</dt>
                <dd>{formatDate(memory.verified_at)}</dd>
              </div>

              <div>
                <dt>Updated</dt>
                <dd>{formatDate(memory.updated_at)}</dd>
              </div>
            </dl>
          </article>

          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  DataHub lineage
                </p>
                <h3>Related assets</h3>
              </div>

              <span className="relay-count-badge">
                {memory.related_asset_urns.length}
              </span>
            </div>

            {memory.related_asset_urns.length === 0 ? (
              <div className="relay-empty-state relay-empty-state-small">
                No related assets were preserved.
              </div>
            ) : (
              <div className="relay-memory-asset-list">
                {memory.related_asset_urns.map((assetUrn) => (
                  <div key={assetUrn}>
                    <span>Related asset</span>
                    <strong>{assetUrn}</strong>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Retrieval signals
                </p>
                <h3>Keywords</h3>
              </div>
            </div>

            <div className="relay-keyword-list">
              {memory.keywords.map((keyword) => (
                <span key={keyword}>{keyword}</span>
              ))}
            </div>
          </article>

          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Traceability
                </p>
                <h3>Source records</h3>
              </div>
            </div>

            <dl className="relay-definition-list">
              <div>
                <dt>Investigation</dt>
                <dd title={memory.originating_investigation_id}>
                  {truncateId(
                    memory.originating_investigation_id,
                  )}
                </dd>
              </div>

              <div>
                <dt>Evidence records</dt>
                <dd>{memory.evidence_ids.length}</dd>
              </div>

              <div>
                <dt>Supersedes</dt>
                <dd>
                  {memory.supersedes_memory_id
                    ? truncateId(memory.supersedes_memory_id)
                    : "No previous version"}
                </dd>
              </div>
            </dl>

            {onOpenInvestigation && (
              <button
                className="relay-secondary-button relay-full-width-button"
                type="button"
                onClick={() =>
                  onOpenInvestigation(
                    memory.originating_investigation_id,
                  )
                }
              >
                Open source investigation
              </button>
            )}
          </article>
        </aside>
      </div>
    </section>
  );
}