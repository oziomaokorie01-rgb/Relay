import type {
  AgentName,
  InvestigationStatus,
} from "../types/api";

interface AgentPipelineProps {
  status: InvestigationStatus;
  currentAgent: string | null;
}

interface PipelineStage {
  id: AgentName;
  label: string;
  description: string;
}

const PIPELINE_STAGES: PipelineStage[] = [
  {
    id: "investigator",
    label: "Investigator",
    description: "Finds the root cause and supporting evidence.",
  },
  {
    id: "repair",
    label: "Repair",
    description: "Creates a supported remediation proposal.",
  },
  {
    id: "reviewer",
    label: "Reviewer",
    description: "Checks evidence, risk, and governance.",
  },
  {
    id: "human",
    label: "Human",
    description: "Approves, rejects, or requests revision.",
  },
  {
    id: "archivist",
    label: "Archivist",
    description: "Creates verified organizational memory.",
  },
];

function getStageIndex(stage: AgentName): number {
  return PIPELINE_STAGES.findIndex(
    (pipelineStage) => pipelineStage.id === stage,
  );
}

function getStatusStage(
  status: InvestigationStatus,
): AgentName | null {
  switch (status) {
    case "queued":
    case "gathering_context":
    case "investigating":
      return "investigator";

    case "repairing":
      return "repair";

    case "reviewing":
      return "reviewer";

    case "awaiting_approval":
      return "human";

    case "archiving":
    case "completed":
      return "archivist";

    default:
      return null;
  }
}

function normalizeAgent(
  currentAgent: string | null,
  status: InvestigationStatus,
): AgentName | null {
  if (
    currentAgent &&
    PIPELINE_STAGES.some(
      (stage) => stage.id === currentAgent,
    )
  ) {
    return currentAgent as AgentName;
  }

  return getStatusStage(status);
}

export default function AgentPipeline({
  status,
  currentAgent,
}: AgentPipelineProps) {
  const activeAgent = normalizeAgent(currentAgent, status);
  const activeIndex = activeAgent
    ? getStageIndex(activeAgent)
    : -1;

  const isCompleted = status === "completed";
  const isFailed = status === "failed";
  const isCancelled = status === "cancelled";

  return (
    <section className="relay-agent-pipeline">
      <header className="relay-agent-pipeline-header">
        <div>
          <p className="relay-eyebrow">
            Multi-agent orchestration
          </p>

          <h3>Investigation pipeline</h3>
        </div>

        <span
          className={`relay-agent-pipeline-state is-${status}`}
        >
          {isCompleted
            ? "Workflow completed"
            : isFailed
              ? "Workflow failed"
              : isCancelled
                ? "Workflow cancelled"
                : "Workflow active"}
        </span>
      </header>

      <div className="relay-agent-pipeline-track">
        {PIPELINE_STAGES.map((stage, index) => {
          const isActive =
            !isCompleted &&
            !isFailed &&
            !isCancelled &&
            index === activeIndex;

          const isComplete =
            isCompleted || index < activeIndex;

          const isPending =
            !isActive && !isComplete;

          return (
            <article
              className={[
                "relay-agent-stage",
                isActive ? "is-active" : "",
                isComplete ? "is-complete" : "",
                isPending ? "is-pending" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              key={stage.id}
            >
              <div className="relay-agent-stage-marker">
                {isComplete ? "✓" : index + 1}
              </div>

              <div className="relay-agent-stage-content">
                <strong>{stage.label}</strong>
                <p>{stage.description}</p>
              </div>

              {index < PIPELINE_STAGES.length - 1 && (
                <span
                  className={`relay-agent-stage-connector ${
                    isComplete ? "is-complete" : ""
                  }`}
                />
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}