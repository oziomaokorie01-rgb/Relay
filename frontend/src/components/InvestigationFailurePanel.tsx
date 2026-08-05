import type {
  InvestigationStatus,
} from "../types/api";

interface InvestigationFailurePanelProps {
  status: InvestigationStatus;
  failureMessage: string | null;
  assetUrn: string;
  onClose: () => void;
}

function getFailureGuidance(
  failureMessage: string | null,
): string {
  const normalizedMessage =
    failureMessage?.toLowerCase() ?? "";

  if (
    normalizedMessage.includes("asset") &&
    normalizedMessage.includes("not found")
  ) {
    return (
      "The selected asset does not exist in the current DataHub " +
      "gateway. Return to the dashboard and choose an asset from " +
      "DataHub search instead of entering an unknown URN."
    );
  }

  if (normalizedMessage.includes("datahub")) {
    return (
      "Relay could not retrieve the required DataHub context. " +
      "Check the backend connection and confirm the asset is available."
    );
  }

  return (
    "Review the failure message and activity timeline, then create " +
    "a new investigation after correcting the incident details."
  );
}

export default function InvestigationFailurePanel({
  status,
  failureMessage,
  assetUrn,
  onClose,
}: InvestigationFailurePanelProps) {
  if (status !== "failed") {
    return null;
  }

  return (
    <section
      className="relay-investigation-failure-panel"
      role="alert"
    >
      <div className="relay-investigation-failure-icon">
        !
      </div>

      <div className="relay-investigation-failure-copy">
        <p className="relay-eyebrow">
          Investigation stopped
        </p>

        <h3>
          Relay could not complete this investigation
        </h3>

        <p className="relay-investigation-failure-message">
          {failureMessage ??
            "The workflow failed before Relay could produce a result."}
        </p>

        <dl>
          <div>
            <dt>Selected asset</dt>
            <dd>{assetUrn}</dd>
          </div>

          <div>
            <dt>What to do next</dt>
            <dd>
              {getFailureGuidance(failureMessage)}
            </dd>
          </div>
        </dl>
      </div>

      <button
        className="relay-secondary-button"
        type="button"
        onClick={onClose}
      >
        Return to investigations
      </button>
    </section>
  );
}