import { useMemo } from "react";

import type {
  AgentActivity,
} from "../types/api";

interface InvestigationActivityTimelineProps {
  activities: AgentActivity[];
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
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
    timeStyle: "medium",
  }).format(date);
}

function formatDuration(
  durationMs: number | null,
): string | null {
  if (
    durationMs === null ||
    durationMs === undefined
  ) {
    return null;
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  const seconds = durationMs / 1000;

  if (seconds < 60) {
    return `${seconds.toFixed(1)} sec`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(
    seconds % 60,
  );

  return `${minutes} min ${remainingSeconds} sec`;
}

function getPayloadEntries(
  payload: Record<string, unknown> | null,
): Array<[string, string]> {
  if (!payload) {
    return [];
  }

  return Object.entries(payload).map(
    ([key, value]) => [
      formatLabel(key),
      typeof value === "string"
        ? value
        : JSON.stringify(value),
    ],
  );
}

export default function InvestigationActivityTimeline({
  activities,
}: InvestigationActivityTimelineProps) {
  const orderedActivities = useMemo(
    () =>
      [...activities].sort(
        (left, right) =>
          new Date(left.started_at).getTime() -
          new Date(right.started_at).getTime(),
      ),
    [activities],
  );

  if (orderedActivities.length === 0) {
    return (
      <div className="relay-empty-state">
        No investigation activity has been recorded yet.
      </div>
    );
  }

  return (
    <div className="relay-activity-timeline">
      {orderedActivities.map(
        (activity, index) => {
          const isLatest =
            index === orderedActivities.length - 1;

          const duration = formatDuration(
            activity.duration_ms,
          );

          const payloadEntries =
            getPayloadEntries(
              activity.structured_payload,
            );

          return (
            <article
              className={[
                "relay-activity-entry",
                isLatest ? "is-latest" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              key={activity.id}
            >
              <div className="relay-activity-rail">
                <span
                  className={`relay-activity-dot is-${activity.status}`}
                />

                {index <
                  orderedActivities.length - 1 && (
                  <span className="relay-activity-line" />
                )}
              </div>

              <div className="relay-activity-entry-content">
                <header className="relay-activity-entry-header">
                  <div>
                    <strong>
                      {formatLabel(
                        activity.agent_name,
                      )}
                    </strong>

                    <span
                      className={`relay-status-badge is-${activity.status}`}
                    >
                      {formatLabel(activity.status)}
                    </span>

                    {isLatest && (
                      <span className="relay-activity-latest-badge">
                        Latest
                      </span>
                    )}
                  </div>

                  <time
                    dateTime={activity.started_at}
                  >
                    {formatDate(
                      activity.started_at,
                    )}
                  </time>
                </header>

                <div className="relay-activity-entry-body">
                  <h4>
                    {formatLabel(
                      activity.event_type,
                    )}
                  </h4>

                  <p>{activity.message}</p>
                </div>

                <footer className="relay-activity-entry-footer">
                  {duration && (
                    <span>
                      Duration: {duration}
                    </span>
                  )}

                  {activity.completed_at && (
                    <span>
                      Completed{" "}
                      {formatDate(
                        activity.completed_at,
                      )}
                    </span>
                  )}
                </footer>

                {payloadEntries.length > 0 && (
                  <details className="relay-activity-details">
                    <summary>
                      View event details
                    </summary>

                    <dl>
                      {payloadEntries.map(
                        ([label, value]) => (
                          <div key={label}>
                            <dt>{label}</dt>
                            <dd>{value}</dd>
                          </div>
                        ),
                      )}
                    </dl>
                  </details>
                )}
              </div>
            </article>
          );
        },
      )}
    </div>
  );
}