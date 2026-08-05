import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { FormEvent, ReactElement } from "react";

import InvestigationWorkspace from "./components/InvestigationWorkspace";
import MemoryCard from "./components/MemoryCard";
import SystemStatus from "./components/SystemStatus";
import InvestigationTemplatePicker from "./components/InvestigationTemplatePicker";
import InvestigationToolbar from "./components/InvestigationToolbar";
import MemoryImpactSummary from "./components/MemoryImpactSummary";
import MemoryLibraryToolbar from "./components/MemoryLibraryToolbar";
import MemoryWorkspace from "./components/MemoryWorkspace";
import useMemoryMetrics from "./hooks/useMemoryMetrics";

import {
  ApiError,
  createInvestigation,
  listInvestigations,
  listMemories,
  runInvestigation,
} from "./lib/api";

import type {
  InvestigationCreateInput,
  InvestigationPriority,
  InvestigationStatus,
  InvestigationSummary,
  RelayMemory,
} from "./types/api";
import useInvestigationPolling from "./hooks/useInvestigationPolling";
// DataHubAssetPicker component may not exist in all setups. Provide a
// lightweight local fallback to avoid build errors while preserving the
// expected API (value, onChange).
let DataHubAssetPicker = ({
  value,
  onChange,
}: {
  value: string;
  onChange: (assetUrn: string) => void;
}): ReactElement => {
  return (
    <label>
      <span>DataHub asset URN</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="urn:li:dashboard:(looker,revenue_dashboard)"
      />
    </label>
  );
};

type WorkspaceView =
  | "dashboard"
  | "investigations"
  | "memories";

type MemorySortOrder =
  | "newest"
  | "confidence"
  | "most_reused";

const DEFAULT_FORM: InvestigationCreateInput = {
  title: "",
  description: "",
  asset_urn: "urn:li:dashboard:(looker,revenue_dashboard)",
  priority: "high",
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred.";
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function confidenceLabel(value: number | null): string {
  if (value === null) {
    return "Not scored";
  }

  return `${Math.round(value * 100)}%`;
}

export default function App() {
  const [view, setView] =
    useState<WorkspaceView>("dashboard");

  const [
    selectedInvestigationId,
    setSelectedInvestigationId,
  ] = useState<string | null>(null);

  const [selectedMemoryId, setSelectedMemoryId] =
    useState<string | null>(null);

  const [investigations, setInvestigations] = useState<
    InvestigationSummary[]
  >([]);

  const [memories, setMemories] = useState<RelayMemory[]>(
    [],
  );

  const {
    metricsByMemoryId,
    isLoading: isLoadingMemoryMetrics,
    error: memoryMetricsError,
    refresh: refreshMemoryMetrics,
  } = useMemoryMetrics(memories);

  const [form, setForm] =
    useState<InvestigationCreateInput>(DEFAULT_FORM);

  const [memorySearchQuery, setMemorySearchQuery] =
    useState("");

  const [memoryIncidentType, setMemoryIncidentType] =
    useState("all");

  const [memorySortOrder, setMemorySortOrder] =
    useState<MemorySortOrder>("newest");
const [investigationSearchQuery, setInvestigationSearchQuery] =
  useState("");

const [investigationStatus, setInvestigationStatus] =
  useState<InvestigationStatus | "all">("all");

const [investigationPriority, setInvestigationPriority] =
  useState<InvestigationPriority | "all">("all"); 
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
const [isCreatingAndRunning, setIsCreatingAndRunning] =
  useState(false);
  const [runningId, setRunningId] = useState<
    string | null
  >(null);

  const [error, setError] = useState<string | null>(
    null,
  );

  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [investigationItems, memoryItems] =
        await Promise.all([
          listInvestigations(),
          listMemories(),
        ]);

      setInvestigations(investigationItems);
      setMemories(memoryItems);
    } catch (loadError) {
      setError(getErrorMessage(loadError));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);
useEffect(() => {
  setError(null);
  setSuccessMessage(null);
}, [view]);
  
// Poll investigations for status updates. No single "data" object is
// available here, so pass undefined for status and let the hook handle
// polling of all investigations via the provided refresh callback.
useInvestigationPolling({
  status: undefined as unknown as string,
  refresh: loadWorkspace,
});
  const activeInvestigations = useMemo(
    () =>
      investigations.filter(
        (investigation) =>
          ![
            "completed",
            "failed",
            "cancelled",
          ].includes(investigation.status),
      ),
    [investigations],
  );

  const awaitingApprovalCount = useMemo(
    () =>
      investigations.filter(
        (investigation) =>
          investigation.status === "awaiting_approval",
      ).length,
    [investigations],
  );

  const completedCount = useMemo(
    () =>
      investigations.filter(
        (investigation) =>
          investigation.status === "completed",
      ).length,
    [investigations],
  );
const filteredInvestigations = useMemo(() => {
  const normalizedQuery =
    investigationSearchQuery.trim().toLowerCase();

  return investigations.filter((investigation) => {
    const matchesStatus =
      investigationStatus === "all" ||
      investigation.status === investigationStatus;

    const matchesPriority =
      investigationPriority === "all" ||
      investigation.priority === investigationPriority;

    if (!matchesStatus || !matchesPriority) {
      return false;
    }

    if (!normalizedQuery) {
      return true;
    }

    const searchableText = [
      investigation.title,
      investigation.asset_urn,
      investigation.status,
      investigation.priority,
      investigation.current_agent ?? "",
    ]
      .join(" ")
      .toLowerCase();

    return searchableText.includes(normalizedQuery);
  });
}, [
  investigations,
  investigationSearchQuery,
  investigationStatus,
  investigationPriority,
]);
  const memoryIncidentTypes = useMemo(
    () =>
      Array.from(
        new Set(
          memories
            .map((memory) => memory.incident_type)
            .filter(Boolean),
        ),
      ).sort(),
    [memories],
  );

  const filteredMemories = useMemo(() => {
    const normalizedQuery =
      memorySearchQuery.trim().toLowerCase();

    const filtered = memories.filter((memory) => {
      const matchesIncidentType =
        memoryIncidentType === "all" ||
        memory.incident_type === memoryIncidentType;

      if (!matchesIncidentType) {
        return false;
      }

      if (!normalizedQuery) {
        return true;
      }

      const searchableText = [
        memory.title,
        memory.summary,
        memory.root_cause,
        memory.resolution,
        memory.primary_asset_urn,
        memory.incident_type,
        ...memory.keywords,
        ...memory.related_asset_urns,
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(normalizedQuery);
    });

    return [...filtered].sort((left, right) => {
      if (memorySortOrder === "confidence") {
        return right.confidence - left.confidence;
      }

      if (memorySortOrder === "most_reused") {
        const rightReuseCount =
          metricsByMemoryId[right.id]
            ?.acceptedReuseCount ?? 0;

        const leftReuseCount =
          metricsByMemoryId[left.id]
            ?.acceptedReuseCount ?? 0;

        return rightReuseCount - leftReuseCount;
      }

      return (
        new Date(right.created_at).getTime() -
        new Date(left.created_at).getTime()
      );
    });
  }, [
    memories,
    memorySearchQuery,
    memoryIncidentType,
    memorySortOrder,
    metricsByMemoryId,
  ]);
function getCleanInvestigationInput():
  | InvestigationCreateInput
  | null {
  const title = form.title.trim();
  const description = form.description.trim();
  const assetUrn = form.asset_urn.trim();

  if (!title) {
    setError("Enter an investigation title.");
    return null;
  }

  if (!description) {
    setError(
      "Describe the incident Relay should investigate.",
    );
    return null;
  }

  if (!assetUrn) {
    setError("Select or enter a DataHub asset URN.");
    return null;
  }

  return {
    ...form,
    title,
    description,
    asset_urn: assetUrn,
  };
}
 async function handleCreateInvestigation(
  event: FormEvent<HTMLFormElement>,
) {
  event.preventDefault();

  setError(null);
  setSuccessMessage(null);

  const cleanInput = getCleanInvestigationInput();

  if (!cleanInput) {
    return;
  }

  setIsCreating(true);

  try {
    const created =
      await createInvestigation(cleanInput);

    setSuccessMessage(
      `Investigation created with status ${created.status}.`,
    );

    setForm(DEFAULT_FORM);
    await loadWorkspace();
    setView("investigations");
  } catch (createError) {
    setError(getErrorMessage(createError));
  } finally {
    setIsCreating(false);
  }
}
async function handleCreateAndRunInvestigation() {
  setError(null);
  setSuccessMessage(null);

  const cleanInput = getCleanInvestigationInput();

  if (!cleanInput) {
    return;
  }

  setIsCreatingAndRunning(true);

  try {
    const created =
      await createInvestigation(cleanInput);

    setForm(DEFAULT_FORM);

    // Open the workspace immediately so the user can
    // watch the agent pipeline progress.
    setSelectedInvestigationId(created.id);

    await runInvestigation(created.id);
    await loadWorkspace();
  } catch (launchError) {
    setError(getErrorMessage(launchError));
  } finally {
    setIsCreatingAndRunning(false);
  }
}
  async function handleRunInvestigation(
  investigationId: string,
) {
  setRunningId(investigationId);
  setError(null);
  setSuccessMessage(null);

  // Open the workspace immediately so the user can watch
  // Investigator → Repair → Reviewer progress live.
  setSelectedInvestigationId(investigationId);

  try {
    const result =
      await runInvestigation(investigationId);

    setSuccessMessage(
      `Investigation advanced to ${formatLabel(
        result.status,
      )}.`,
    );

    await loadWorkspace();
  } catch (runError) {
    setError(getErrorMessage(runError));

    // Keep the workspace open so the failure state and
    // activity timeline remain visible.
  } finally {
    setRunningId(null);
  }
}

  if (selectedMemoryId) {
    return (
      <div className="relay-app">
        <aside className="relay-sidebar">
          <div className="relay-brand">
            <div className="relay-brand-mark">R</div>

            <div>
              <strong>Relay</strong>
              <span>Operational Memory</span>
            </div>
          </div>

          <nav className="relay-navigation">
            <button
              type="button"
              onClick={() => {
                setSelectedMemoryId(null);
                setView("dashboard");
              }}
            >
              Dashboard
            </button>

            <button
              type="button"
              onClick={() => {
                setSelectedMemoryId(null);
                setView("investigations");
              }}
            >
              Investigations
            </button>

            <button
              className="is-active"
              type="button"
              onClick={() => {
                setSelectedMemoryId(null);
                setView("memories");
              }}
            >
              Memory Library
            </button>
          </nav>

          <div className="relay-sidebar-footer">
  <SystemStatus />
</div>
        </aside>

        <main className="relay-main">
          <MemoryWorkspace
            memoryId={selectedMemoryId}
            onClose={() => {
              setSelectedMemoryId(null);
              setView("memories");
            }}
            onOpenInvestigation={(investigationId) => {
              setSelectedMemoryId(null);
              setSelectedInvestigationId(
                investigationId,
              );
            }}
          />
        </main>
      </div>
    );
  }

  if (selectedInvestigationId) {
    return (
      <div className="relay-app">
        <aside className="relay-sidebar">
          <div className="relay-brand">
            <div className="relay-brand-mark">R</div>

            <div>
              <strong>Relay</strong>
              <span>Operational Memory</span>
            </div>
          </div>

          <nav className="relay-navigation">
            <button
              type="button"
              onClick={() => {
                setSelectedInvestigationId(null);
                setView("dashboard");
              }}
            >
              Dashboard
            </button>

            <button
              className="is-active"
              type="button"
              onClick={() => {
                setSelectedInvestigationId(null);
                setView("investigations");
              }}
            >
              Investigations
            </button>

            <button
              type="button"
              onClick={() => {
                setSelectedInvestigationId(null);
                setSelectedMemoryId(null);
                setView("memories");
              }}
            >
              Memory Library
            </button>
          </nav>

         <div className="relay-sidebar-footer">
  <SystemStatus />
</div>
        </aside>

        <main className="relay-main">
          <InvestigationWorkspace
            investigationId={selectedInvestigationId}
            onClose={() => {
              setSelectedInvestigationId(null);
              setView("investigations");
            }}
            onInvestigationChanged={loadWorkspace}
            onMemoryCreated={() => {
              void loadWorkspace();
            }}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="relay-app">
      <aside className="relay-sidebar">
        <div className="relay-brand">
          <div className="relay-brand-mark">R</div>

          <div>
            <strong>Relay</strong>
            <span>Operational Memory</span>
          </div>
        </div>

        <nav className="relay-navigation">
          <button
            className={
              view === "dashboard" ? "is-active" : ""
            }
            type="button"
            onClick={() => setView("dashboard")}
          >
            Dashboard
          </button>

          <button
            className={
              view === "investigations"
                ? "is-active"
                : ""
            }
            type="button"
            onClick={() => setView("investigations")}
          >
            Investigations
          </button>

          <button
            className={
              view === "memories" ? "is-active" : ""
            }
            type="button"
            onClick={() => setView("memories")}
          >
            Memory Library
          </button>
        </nav>

        <div className="relay-sidebar-footer">
  <SystemStatus />
</div>
      </aside>

      <main className="relay-main">
        <header className="relay-header">
          <div>
            <p className="relay-eyebrow">
              Collaborative operational intelligence
            </p>

            <h1>
              {view === "dashboard" &&
                "Investigation Command Center"}

              {view === "investigations" &&
                "Investigations"}

              {view === "memories" &&
                "Verified Memory Library"}
            </h1>
          </div>

          <button
            className="relay-refresh-button"
            type="button"
            disabled={isLoading}
            onClick={() => void loadWorkspace()}
          >
            {isLoading ? "Refreshing…" : "Refresh"}
          </button>
        </header>

        {error && (
          <div className="relay-alert relay-alert-error">
            <strong>
              Relay encountered a problem.
            </strong>
            <span>{error}</span>
          </div>
        )}

        {successMessage && (
          <div className="relay-alert relay-alert-success">
            <strong>Success</strong>
            <span>{successMessage}</span>
          </div>
        )}

        {view === "dashboard" && (
          <>
            <section className="relay-stat-grid">
              <article className="relay-stat-card">
                <span>Active investigations</span>
                <strong>
                  {activeInvestigations.length}
                </strong>
                <small>
                  Across the current workflow
                </small>
              </article>

              <article className="relay-stat-card">
                <span>Awaiting approval</span>
                <strong>{awaitingApprovalCount}</strong>
                <small>
                  Human decisions required
                </small>
              </article>

              <article className="relay-stat-card">
                <span>Verified memories</span>
                <strong>{memories.length}</strong>
                <small>
                  Available to future agents
                </small>
              </article>

              <article className="relay-stat-card">
                <span>Completed cases</span>
                <strong>{completedCount}</strong>
                <small>
                  Archived investigation records
                </small>
              </article>
            </section>
<MemoryImpactSummary
  memories={memories}
  metricsByMemoryId={metricsByMemoryId}
  isLoading={isLoadingMemoryMetrics}
/>

            <section className="relay-dashboard-grid">
              <article className="relay-panel">
                <div className="relay-panel-heading">
                  <div>
                    <p className="relay-eyebrow">
                      Start an investigation
                    </p>

                    <h2>
                      Describe the operational incident
                    </h2>
                  </div>
                </div>
<InvestigationTemplatePicker
  onSelect={(template) => {
    setForm(template);
    setError(null);
    setSuccessMessage(
      "Investigation template loaded. Review the details before creating it.",
    );
  }}
/>
                <form
                  className="relay-investigation-form"
                  onSubmit={handleCreateInvestigation}
                >
                  <label>
                    <span>Investigation title</span>

                    <input
                      value={form.title}
                      maxLength={240}
                      placeholder="Revenue dashboard dropped by 35%"
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          title: event.target.value,
                        }))
                      }
                    />
                  </label>

                  <label>
                    <span>Description</span>

                    <textarea
                      value={form.description}
                      rows={5}
                      placeholder="Explain what changed, when it started, and why it matters."
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          description:
                            event.target.value,
                        }))
                      }
                    />
                  </label>

                  <DataHubAssetPicker
  value={form.asset_urn}
  onChange={(assetUrn) =>
    setForm((current) => ({
      ...current,
      asset_urn: assetUrn,
    }))
  }
/>
                  <label>
                    <span>Priority</span>

                    <select
                      value={form.priority}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          priority:
                            event.target
                              .value as InvestigationPriority,
                        }))
                      }
                    >
                      <option value="low">Low</option>
                      <option value="medium">
                        Medium
                      </option>
                      <option value="high">
                        High
                      </option>
                    </select>
                  </label>

                  <div className="relay-investigation-launch-actions">
  <button
    className="relay-secondary-button"
    type="submit"
    disabled={
      isCreating ||
      isCreatingAndRunning
    }
  >
    {isCreating
      ? "Creating…"
      : "Create draft"}
  </button>

  <button
    className="relay-primary-button"
    type="button"
    disabled={
      isCreating ||
      isCreatingAndRunning
    }
    onClick={() =>
      void handleCreateAndRunInvestigation()
    }
  >
    {isCreatingAndRunning
      ? "Launching agents…"
      : "Create & run"}
  </button>
</div>
                </form>
              </article>

              <article className="relay-panel">
                <div className="relay-panel-heading">
                  <div>
                    <p className="relay-eyebrow">
                      Recent activity
                    </p>

                    <h2>Latest investigations</h2>
                  </div>

                  <button
                    type="button"
                    className="relay-text-button"
                    onClick={() =>
                      setView("investigations")
                    }
                  >
                    View all
                  </button>
                </div>

                <InvestigationList
                  investigations={investigations.slice(
                    0,
                    5,
                  )}
                  isLoading={isLoading}
                  runningId={runningId}
                  onRun={handleRunInvestigation}
                  onOpen={
                    setSelectedInvestigationId
                  }
                />
              </article>
            </section>
          </>
        )}

        {view === "investigations" && (
          <section className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <InvestigationToolbar
  searchQuery={investigationSearchQuery}
  status={investigationStatus}
  priority={investigationPriority}
  resultCount={filteredInvestigations.length}
  onSearchChange={setInvestigationSearchQuery}
  onStatusChange={setInvestigationStatus}
  onPriorityChange={setInvestigationPriority}
  onClear={() => {
    setInvestigationSearchQuery("");
    setInvestigationStatus("all");
    setInvestigationPriority("all");
  }}
/>
                <p className="relay-eyebrow">
                  Workflow history
                </p>

                <h2>All investigations</h2>
              </div>

              <span className="relay-count-badge">
                {investigations.length}
              </span>
            </div>

           <InvestigationList
  investigations={filteredInvestigations}
  isLoading={isLoading}
  runningId={runningId}
  onRun={handleRunInvestigation}
  onOpen={setSelectedInvestigationId}
/>
          </section>
        )}

        {view === "memories" && (
          <section className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Verified organizational knowledge
                </p>

                <h2>Memory Library</h2>
              </div>

              <span className="relay-count-badge">
                {memories.length}
              </span>
            </div>

            <MemoryLibraryToolbar
              searchQuery={memorySearchQuery}
              incidentType={memoryIncidentType}
              sortOrder={memorySortOrder}
              incidentTypes={memoryIncidentTypes}
              resultCount={filteredMemories.length}
              onSearchChange={setMemorySearchQuery}
              onIncidentTypeChange={
                setMemoryIncidentType
              }
              onSortOrderChange={setMemorySortOrder}
              onClear={() => {
                setMemorySearchQuery("");
                setMemoryIncidentType("all");
                setMemorySortOrder("newest");
              }}
            />

            {memoryMetricsError && (
              <div className="relay-alert relay-alert-error">
                <strong>
                  Some reuse metrics could not be loaded.
                </strong>

                <span>
                  Memory records are still available, but
                  reuse totals may be incomplete.
                </span>

                <button
                  className="relay-text-button"
                  type="button"
                  onClick={() =>
                    void refreshMemoryMetrics()
                  }
                >
                  Retry metrics
                </button>
              </div>
            )}

            {isLoading ? (
              <div className="relay-empty-state">
                Loading verified memories…
              </div>
            ) : memories.length === 0 ? (
              <div className="relay-empty-state">
                No verified memories exist yet.
                Complete and archive an investigation
                to create the first one.
              </div>
            ) : filteredMemories.length === 0 ? (
              <div className="relay-empty-state">
                No verified memories match the current
                search or filters.
              </div>
            ) : (
              <div className="relay-memory-grid">
                {filteredMemories.map((memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    metrics={
                      metricsByMemoryId[memory.id]
                    }
                    isLoadingMetrics={
                      isLoadingMemoryMetrics
                    }
                    onOpen={setSelectedMemoryId}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

interface InvestigationListProps {
  investigations: InvestigationSummary[];
  isLoading: boolean;
  runningId: string | null;
  onRun: (
    investigationId: string,
  ) => Promise<void>;
  onOpen: (investigationId: string) => void;
}

function InvestigationList({
  investigations,
  isLoading,
  runningId,
  onRun,
  onOpen,
}: InvestigationListProps) {
  if (isLoading) {
    return (
      <div className="relay-empty-state">
        Loading investigations…
      </div>
    );
  }

  if (investigations.length === 0) {
    return (
      <div className="relay-empty-state">
        No investigations have been created yet.
      </div>
    );
  }

  return (
    <div className="relay-investigation-list">
      {investigations.map((investigation) => {
        const canRun =
          investigation.status === "draft";

        const isRunning =
          runningId === investigation.id;

        return (
          <article
            className="relay-investigation-row"
            key={investigation.id}
          >
            <div className="relay-investigation-main">
              <div className="relay-investigation-title-row">
                <h3>{investigation.title}</h3>

                <span
                  className={`relay-status-badge is-${investigation.status}`}
                >
                  {formatLabel(
                    investigation.status,
                  )}
                </span>
              </div>

              <p>{investigation.asset_urn}</p>

              <div className="relay-investigation-meta">
                <span>
                  Priority:{" "}
                  {formatLabel(
                    investigation.priority,
                  )}
                </span>

                <span>
                  Agent:{" "}
                  {investigation.current_agent
                    ? formatLabel(
                        investigation.current_agent,
                      )
                    : "Not started"}
                </span>

                <span>
                  Confidence:{" "}
                  {confidenceLabel(
                    investigation.overall_confidence,
                  )}
                </span>

                <span>
                  Updated{" "}
                  {formatDate(
                    investigation.updated_at,
                  )}
                </span>
              </div>
            </div>

            <div className="relay-investigation-actions">
              <button
                className="relay-secondary-button"
                type="button"
                onClick={() =>
                  onOpen(investigation.id)
                }
              >
                Open
              </button>

              {canRun && (
                <button
                  className="relay-primary-button"
                  type="button"
                  disabled={isRunning}
                  onClick={() =>
                    void onRun(investigation.id)
                  }
                >
                  {isRunning ? "Running…" : "Run"}
                </button>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}