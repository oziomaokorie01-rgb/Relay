import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ApiError,
  archiveInvestigation,
  getInvestigation,
  getInvestigationActivity,
  getInvestigationEvidence,
  getInvestigationMemoryReuse,
  getInvestigationRepair,
  getInvestigationReview,
  submitInvestigationApproval,
} from "../lib/api";
import InvestigationActivityTimeline from "./InvestigationActivityTimeline";
import InvestigationFailurePanel from "./InvestigationFailurePanel";
import LiveInvestigationBanner from "./LiveInvestigationBanner";
import LineageGraph from "./LineageGraph";
import AgentPipeline from "./AgentPipeline";
import CopyButton from "./CopyButton";
import type {
  AgentActivity,
  Evidence,
  InvestigationDetail,
  MemoryReuseEvent,
  RelayMemory,
  RepairProposal,
  Review,
} from "../types/api";
import useInvestigationPolling from "../hooks/useInvestigationPolling";

interface InvestigationWorkspaceProps {
  investigationId: string;
  onClose: () => void;
  onInvestigationChanged?: () => Promise<void> | void;
  onMemoryCreated?: (memory: RelayMemory) => void;
}

type WorkspaceTab =
  | "overview"
  | "evidence"
  | "repair"
  | "review"
  | "activity";

interface WorkspaceData {
  investigation: InvestigationDetail;
  activity: AgentActivity[];
  evidence: Evidence[];
  repair: RepairProposal | null;
  review: Review | null;
  memoryReuse: MemoryReuseEvent[];
}

const EMPTY_DATA: WorkspaceData = {
  investigation: {
    id: "",
    title: "",
    description: "",
    asset_urn: "",
    priority: "low",
    status: "draft",
    current_agent: null,
    overall_confidence: null,
    created_at: "",
    updated_at: "",
    completed_at: null,
    context_snapshot: {},
    root_cause_summary: null,
    failure_message: null,
  },
  activity: [],
  evidence: [],
  repair: null,
  review: null,
  memoryReuse: [],
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

function isMissingResource(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export default function InvestigationWorkspace({
  investigationId,
  onClose,
  onInvestigationChanged,
  onMemoryCreated,
}: InvestigationWorkspaceProps) {
  const [activeTab, setActiveTab] =
    useState<WorkspaceTab>("overview");

  const [data, setData] = useState<WorkspaceData>(EMPTY_DATA);

  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);

  const [approvalNotes, setApprovalNotes] = useState(
    "Approved for organizational reuse.",
  );

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] =
    useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const investigation = await getInvestigation(
        investigationId,
      );

      const [
        activityResult,
        evidenceResult,
        repairResult,
        reviewResult,
        reuseResult,
      ] = await Promise.allSettled([
        getInvestigationActivity(investigationId),
        getInvestigationEvidence(investigationId),
        getInvestigationRepair(investigationId),
        getInvestigationReview(investigationId),
        getInvestigationMemoryReuse(investigationId),
      ]);

      setData({
        investigation,
        activity:
          activityResult.status === "fulfilled"
            ? activityResult.value
            : [],
        evidence:
          evidenceResult.status === "fulfilled"
            ? evidenceResult.value
            : [],
        repair:
          repairResult.status === "fulfilled"
            ? repairResult.value
            : null,
        review:
          reviewResult.status === "fulfilled"
            ? reviewResult.value
            : null,
        memoryReuse:
          reuseResult.status === "fulfilled"
            ? reuseResult.value
            : [],
      });

      const rejectedResults = [
        activityResult,
        evidenceResult,
        repairResult,
        reviewResult,
        reuseResult,
      ].filter(
        (
          result,
        ): result is PromiseRejectedResult =>
          result.status === "rejected",
      );

      const unexpectedFailure = rejectedResults.find(
        (result) => !isMissingResource(result.reason),
      );

      if (unexpectedFailure) {
        setError(getErrorMessage(unexpectedFailure.reason));
      }
    } catch (loadError) {
      setError(getErrorMessage(loadError));
    } finally {
      setIsLoading(false);
    }
  }, [investigationId]);

  const investigation = data.investigation;

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  useInvestigationPolling({
    status: investigation.status,
    refresh: loadWorkspace,
  });

  useEffect(() => {
    if (
      investigation.status === "failed" &&
      (activeTab === "repair" || activeTab === "review")
    ) {
      setActiveTab("overview");
    }
  }, [activeTab, investigation.status]);

  const lineageNodes = useMemo(
    () => investigation.context_snapshot.lineage?.nodes ?? [],
    [investigation.context_snapshot.lineage?.nodes],
  );

  const lineageEdges = useMemo(
    () => investigation.context_snapshot.lineage?.edges ?? [],
    [investigation.context_snapshot.lineage?.edges],
  );

  const inheritedMemory = data.memoryReuse[0] ?? null;

  const canApprove =
    investigation.status === "awaiting_approval";

  const canArchive =
    investigation.status === "archiving";

  async function handleApprove() {
    setIsApproving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await submitInvestigationApproval(
        investigationId,
        {
          decision: "approve",
          edited_title: null,
          edited_summary: null,
          notes: approvalNotes.trim() || null,
        },
      );

      setSuccessMessage(response.message);

      await loadWorkspace();
      await onInvestigationChanged?.();
    } catch (approvalError) {
      setError(getErrorMessage(approvalError));
    } finally {
      setIsApproving(false);
    }
  }

  async function handleRequestRevision() {
    const notes = approvalNotes.trim();

    if (!notes) {
      setError(
        "Enter notes explaining what the Repair Agent must revise.",
      );
      return;
    }

    setIsApproving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await submitInvestigationApproval(
        investigationId,
        {
          decision: "request_revision",
          edited_title: null,
          edited_summary: null,
          notes,
        },
      );

      setSuccessMessage(response.message);

      await loadWorkspace();
      await onInvestigationChanged?.();
    } catch (approvalError) {
      setError(getErrorMessage(approvalError));
    } finally {
      setIsApproving(false);
    }
  }

  async function handleArchive() {
    setIsArchiving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await archiveInvestigation(
        investigationId,
      );

      setSuccessMessage(
        "Verified organizational memory created successfully.",
      );

      onMemoryCreated?.(response.memory);

      await loadWorkspace();
      await onInvestigationChanged?.();
    } catch (archiveError) {
      setError(getErrorMessage(archiveError));
    } finally {
      setIsArchiving(false);
    }
  }

  if (isLoading && !investigation.id) {
    return (
      <section className="relay-workspace">
        <div className="relay-workspace-loading">
          Loading investigation workspace…
        </div>
      </section>
    );
  }

  return (
    <section className="relay-workspace">
      <header className="relay-workspace-header">
        <div>
          <button
            className="relay-back-button"
            type="button"
            onClick={onClose}
          >
            ← Back to investigations
          </button>

          <div className="relay-workspace-title-row">
            <div>
              <p className="relay-eyebrow">
                Investigation workspace
              </p>

              <h2>{investigation.title}</h2>
            </div>

            <span
              className={`relay-status-badge is-${investigation.status}`}
            >
              {formatLabel(investigation.status)}
            </span>
          </div>

          <p className="relay-workspace-description">
            {investigation.description}
          </p>
        </div>

        <button
          className="relay-refresh-button"
          type="button"
          disabled={isLoading}
          onClick={() => void loadWorkspace()}
        >
          {isLoading ? "Refreshing…" : "Refresh workspace"}
        </button>
      </header>

      {error && (
        <div className="relay-alert relay-alert-error">
          <strong>Relay encountered a problem.</strong>
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="relay-alert relay-alert-success">
          <strong>Success</strong>
          <span>{successMessage}</span>
        </div>
      )}
<LiveInvestigationBanner
  status={investigation.status}
  currentAgent={investigation.current_agent}
  isRefreshing={isLoading}
/>
<InvestigationFailurePanel
  status={investigation.status}
  failureMessage={investigation.failure_message}
  assetUrn={investigation.asset_urn}
  onClose={onClose}
/>
      {inheritedMemory && (
        <article className="relay-inherited-memory-banner">
           <div>
            <span className="relay-inherited-memory-icon">↗</span>

            <div>
              <strong>Verified memory inherited</strong>

              <p>
                Relay reused an earlier root-cause precedent with{" "}
                {formatConfidence(
                  inheritedMemory.similarity_score,
                )}{" "}
                similarity.
              </p>
            </div>
          </div>

          <dl>
            <div>
              <dt>Steps skipped</dt>
              <dd>
                {inheritedMemory.estimated_steps_skipped}
              </dd>
            </div>

            <div>
              <dt>Time saved</dt>
              <dd>
                {
                  inheritedMemory.estimated_time_saved_minutes
                }{" "}
                min
              </dd>
            </div>
          </dl>
        </article>
      )}

      <section className="relay-workspace-summary-grid">
        <article>
          <span>Current agent</span>
          <strong>
            {investigation.current_agent
              ? formatLabel(investigation.current_agent)
              : "Not started"}
          </strong>
        </article>

        <article>
          <span>Confidence</span>
          <strong>
            {formatConfidence(
              investigation.overall_confidence,
            )}
          </strong>
        </article>

        <article>
          <span>Priority</span>
          <strong>
            {formatLabel(investigation.priority)}
          </strong>
        </article>

        <article>
          <span>Evidence records</span>
          <strong>{data.evidence.length}</strong>
        </article>

        <article>
          <span>Lineage nodes</span>
          <strong>{lineageNodes.length}</strong>
        </article>
      </section>
      <AgentPipeline
  status={investigation.status}
  currentAgent={investigation.current_agent}
/>

     <nav className="relay-workspace-tabs">
  {(
    investigation.status === "failed"
      ? ([
          "overview",
          "evidence",
          "activity",
        ] as WorkspaceTab[])
      : ([
          "overview",
          "evidence",
          "repair",
          "review",
          "activity",
        ] as WorkspaceTab[])
  ).map((tab) => (
    <button
      key={tab}
      type="button"
      className={activeTab === tab ? "is-active" : ""}
      onClick={() => setActiveTab(tab)}
    >
      {formatLabel(tab)}
    </button>
  ))}
</nav>
      {activeTab === "overview" && (
        <div className="relay-workspace-content-grid">
          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  DataHub context
                </p>
                <h3>Selected asset</h3>
              </div>
            </div>

            <DefinitionList
              items={[
                [
                  "Display name",
                  investigation.context_snapshot.asset
                    ?.display_name ?? "Not available",
                ],
                [
                  "Platform",
                  investigation.context_snapshot.asset
                    ?.platform ?? "Not available",
                ],
                [
                  "Entity type",
                  investigation.context_snapshot.asset
                    ?.entity_type ?? "Not available",
                ],
                [
                  "Domain",
                  investigation.context_snapshot.asset
                    ?.domain ?? "Not available",
                ],
                [
                  "Quality status",
                  investigation.context_snapshot.asset
                    ?.quality_status ?? "Not available",
                ],
                [
                  "Asset URN",
                  investigation.asset_urn,
                ],
              ]}
            />

            <div className="relay-root-cause-block">
              <span>Root-cause summary</span>

              <p>
                {investigation.root_cause_summary ??
                  "The Investigator has not produced a root-cause summary yet."}
              </p>
            </div>
          </article>

          <article className="relay-panel">
            <div className="relay-panel-heading">
              <div>
                <p className="relay-eyebrow">
                  Dependency graph
                </p>
                <h3>Data lineage</h3>
              </div>

              <span className="relay-count-badge">
                {lineageEdges.length} edges
              </span>
            </div>

            {lineageNodes.length === 0 ? (
              <div className="relay-empty-state">
                DataHub lineage has not been loaded yet.
              </div>
            ) : (
              <LineageGraph
  nodes={lineageNodes}
  edges={lineageEdges}
  rootUrn={
    investigation.context_snapshot.asset?.urn ??
    investigation.asset_urn
  }
/>
            )}
          </article>
        </div>
      )}

      {activeTab === "evidence" && (
        <article className="relay-panel">
          <div className="relay-panel-heading">
            <div>
              <p className="relay-eyebrow">
                Investigator findings
              </p>
              <h3>Evidence ledger</h3>
            </div>

            <span className="relay-count-badge">
              {data.evidence.length}
            </span>
          </div>

          {data.evidence.length === 0 ? (
            <div className="relay-empty-state">
              No evidence has been produced yet.
            </div>
          ) : (
            <div className="relay-evidence-list">
              {data.evidence.map((evidence) => (
                <article
                  className="relay-evidence-card"
                  key={evidence.id}
                >
                  <div className="relay-evidence-header">
                    <span>
                      {formatLabel(evidence.type)}
                    </span>

                    <strong>
                      {formatConfidence(evidence.confidence)}
                    </strong>
                  </div>

                  <h4>{evidence.title}</h4>
                  <p>{evidence.description}</p>

                  <footer>
                    <span>
                      Source:{" "}
                      {evidence.source_reference ??
                        "Not specified"}
                    </span>

                    <span>
                      Agent:{" "}
                      {formatLabel(
                        evidence.created_by_agent,
                      )}
                    </span>
                  </footer>
                </article>
              ))}
            </div>
          )}
        </article>
      )}

      {investigation.status !== "failed" &&
activeTab === "repair" && (
        <article className="relay-panel">
          <div className="relay-panel-heading">
            <div>
              <p className="relay-eyebrow">
                Repair Agent
              </p>
              <h3>Proposed remediation</h3>
            </div>

            {data.repair && (
              <span
                className={`relay-status-badge is-${data.repair.status}`}
              >
                {formatLabel(data.repair.status)}
              </span>
            )}
          </div>

          {!data.repair ? (
            <div className="relay-empty-state">
              The Repair Agent has not produced a proposal yet.
            </div>
          ) : (
            <div className="relay-repair-layout">
              <section>
                <h4>Proposal summary</h4>
                <p>{data.repair.summary}</p>

                <h4>Expected outcome</h4>
                <p>{data.repair.expected_outcome}</p>

                <h4>Rollback plan</h4>
                <p>
                  {data.repair.rollback_plan ??
                    "No rollback plan was provided."}
                </p>
              </section>

              <section>
               <div className="relay-code-header">
  <div>
    <span>
      {formatLabel(
        data.repair.artifact_type,
      )}
    </span>

    <span>
      Risk:{" "}
      {formatLabel(data.repair.risk_level)}
    </span>
  </div>

  <CopyButton
    value={data.repair.artifact_content ?? ""}
    idleLabel="Copy artifact"
    successLabel="Copied"
  />
</div>

                <pre className="relay-code-block">
                  <code>
                    {data.repair.artifact_content ??
                      "No generated artifact."}
                  </code>
                </pre>
              </section>

              <section className="relay-repair-tests">
                <h4>Validation tests</h4>

                {data.repair.tests.length === 0 ? (
                  <p>No validation tests were proposed.</p>
                ) : (
                  data.repair.tests.map((test, index) => (
                    <article key={index}>
                      <strong>
                        {String(
                          test.name ??
                            `Validation test ${index + 1}`,
                        )}
                      </strong>

                      <p>
                        {String(
                          test.description ??
                            "No test description.",
                        )}
                      </p>
                    </article>
                  ))
                )}
              </section>
            </div>
          )}
        </article>
      )}

      {investigation.status !== "failed" &&
activeTab === "review" && (
        <article className="relay-panel">
          <div className="relay-panel-heading">
            <div>
              <p className="relay-eyebrow">
                Reviewer Agent
              </p>
              <h3>Verification decision</h3>
            </div>

            {data.review && (
              <span className="relay-status-badge is-verified">
                {formatLabel(data.review.decision)}
              </span>
            )}
          </div>

          {!data.review ? (
            <div className="relay-empty-state">
              The Reviewer has not evaluated this proposal yet.
            </div>
          ) : (
            <>
              <div className="relay-review-grid">
                <ReviewCheckCard
                  title="Evidence coverage"
                  check={data.review.evidence_coverage}
                />

                <ReviewCheckCard
                  title="Schema compatibility"
                  check={data.review.schema_compatibility}
                />

                <ReviewCheckCard
                  title="Downstream risk"
                  check={data.review.downstream_risk}
                />

                <ReviewCheckCard
                  title="Governance compliance"
                  check={data.review.governance_compliance}
                />
              </div>

              <div className="relay-review-summary">
                <strong>
                  Reviewer confidence:{" "}
                  {formatConfidence(
                    data.review.confidence,
                  )}
                </strong>

                <p>
                  {data.review.notes ??
                    "No Reviewer summary was provided."}
                </p>
              </div>

              {data.review.conditions.length > 0 && (
                <section className="relay-review-conditions">
                  <h4>Conditions</h4>

                  <ul>
                    {data.review.conditions.map((condition) => (
                      <li key={condition}>{condition}</li>
                    ))}
                  </ul>
                </section>
              )}

              {canApprove && (
                <section className="relay-human-approval-panel">
                  <div>
                    <p className="relay-eyebrow">
                      Human checkpoint
                    </p>

                    <h4>Approve organizational reuse</h4>

                    <p>
                      A human decision is required before the
                      Archivist can create verified memory.
                    </p>
                  </div>

                  <label>
                    <span>Decision notes</span>

                    <textarea
                      rows={4}
                      value={approvalNotes}
                      onChange={(event) =>
                        setApprovalNotes(
                          event.target.value,
                        )
                      }
                    />
                  </label>

                  <div className="relay-approval-actions">
                    <button
                      className="relay-secondary-button"
                      type="button"
                      disabled={isApproving}
                      onClick={() =>
                        void handleRequestRevision()
                      }
                    >
                      Request revision
                    </button>

                    <button
                      className="relay-primary-button"
                      type="button"
                      disabled={isApproving}
                      onClick={() => void handleApprove()}
                    >
                      {isApproving
                        ? "Submitting…"
                        : "Approve investigation"}
                    </button>
                  </div>
                </section>
              )}

              {canArchive && (
                <section className="relay-human-approval-panel">
                  <div>
                    <p className="relay-eyebrow">
                      Archivist ready
                    </p>

                    <h4>Create verified memory</h4>

                    <p>
                      Human approval is recorded. The investigation
                      can now be converted into reusable
                      organizational knowledge.
                    </p>
                  </div>

                  <button
                    className="relay-primary-button"
                    type="button"
                    disabled={isArchiving}
                    onClick={() => void handleArchive()}
                  >
                    {isArchiving
                      ? "Creating memory…"
                      : "Archive as verified memory"}
                  </button>
                </section>
              )}
            </>
          )}
        </article>
      )}

     {activeTab === "activity" && (
  <article className="relay-panel">
    <div className="relay-panel-heading">
      <div>
        <p className="relay-eyebrow">
          Agent trace
        </p>

        <h3>Activity timeline</h3>
      </div>

      <span className="relay-count-badge">
        {data.activity.length}
      </span>
    </div>

    <InvestigationActivityTimeline
      activities={data.activity}
    />
  </article>
)}
      <footer className="relay-workspace-footer">
        <span>
          Created {formatDate(investigation.created_at)}
        </span>

        <span>
          Updated {formatDate(investigation.updated_at)}
        </span>

        {investigation.completed_at && (
          <span>
            Completed{" "}
            {formatDate(investigation.completed_at)}
          </span>
        )}
      </footer>
    </section>
  );
}

interface DefinitionListProps {
  items: Array<[string, string]>;
}

function DefinitionList({
  items,
}: DefinitionListProps) {
  return (
    <dl className="relay-definition-list">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

interface ReviewCheckCardProps {
  title: string;
  check: {
    status: "pass" | "warning" | "fail";
    explanation: string;
  };
}

function ReviewCheckCard({
  title,
  check,
}: ReviewCheckCardProps) {
  return (
    <article
      className={`relay-review-check is-${check.status}`}
    >
      <header>
        <h4>{title}</h4>
        <span>{formatLabel(check.status)}</span>
      </header>

      <p>{check.explanation}</p>
    </article>
  );
}