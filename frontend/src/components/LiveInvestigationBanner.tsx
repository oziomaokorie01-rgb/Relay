import type {
  InvestigationStatus,
} from "../types/api";

interface LiveInvestigationBannerProps {
  status: InvestigationStatus;
  currentAgent: string | null;
  isRefreshing: boolean;
}

const ACTIVE_STATUSES = new Set<InvestigationStatus>([
  "queued",
  "gathering_context",
  "investigating",
  "repairing",
  "reviewing",
  "archiving",
]);

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function getStatusMessage(
  status: InvestigationStatus,
): string {
  switch (status) {
    case "queued":
      return "Relay has queued this investigation.";

    case "gathering_context":
      return "Relay is gathering DataHub metadata and lineage context.";

    case "investigating":
      return "The Investigator is tracing the failure and collecting evidence.";

    case "repairing":
      return "The Repair Agent is preparing a supported remediation.";

    case "reviewing":
      return "The Reviewer is checking evidence, risk, and governance.";

    case "archiving":
      return "The Archivist is creating verified organizational memory.";

    default:
      return "Relay is processing this investigation.";
  }
}

export default function LiveInvestigationBanner({
  status,
  currentAgent,
  isRefreshing,
}: LiveInvestigationBannerProps) {
  if (!ACTIVE_STATUSES.has(status)) {
    return null;
  }

  const agentLabel = currentAgent
    ? formatLabel(currentAgent)
    : "Relay";

  return (
    <section
      className="relay-live-investigation-banner"
      aria-live="polite"
    >
      <div className="relay-live-investigation-indicator">
        <span />
      </div>

      <div className="relay-live-investigation-copy">
        <div>
          <strong>{agentLabel} is working</strong>

          <span
            className={`relay-status-badge is-${status}`}
          >
            {formatLabel(status)}
          </span>
        </div>

        <p>{getStatusMessage(status)}</p>
      </div>

      <div className="relay-live-investigation-refresh">
        <span className={isRefreshing ? "is-active" : ""}>
          ↻
        </span>

        <small>
          {isRefreshing
            ? "Updating workspace…"
            : "Live updates enabled"}
        </small>
      </div>
    </section>
  );
}