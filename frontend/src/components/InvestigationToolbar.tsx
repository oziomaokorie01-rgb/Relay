import type {
  InvestigationPriority,
  InvestigationStatus,
} from "../types/api";

interface InvestigationToolbarProps {
  searchQuery: string;
  status: InvestigationStatus | "all";
  priority: InvestigationPriority | "all";
  resultCount: number;
  onSearchChange: (value: string) => void;
  onStatusChange: (
    value: InvestigationStatus | "all",
  ) => void;
  onPriorityChange: (
    value: InvestigationPriority | "all",
  ) => void;
  onClear: () => void;
}

const STATUS_OPTIONS: InvestigationStatus[] = [
  "draft",
  "queued",
  "gathering_context",
  "investigating",
  "repairing",
  "reviewing",
  "awaiting_approval",
  "archiving",
  "completed",
  "failed",
  "cancelled",
];

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

export default function InvestigationToolbar({
  searchQuery,
  status,
  priority,
  resultCount,
  onSearchChange,
  onStatusChange,
  onPriorityChange,
  onClear,
}: InvestigationToolbarProps) {
  const hasActiveFilters =
    searchQuery.trim().length > 0 ||
    status !== "all" ||
    priority !== "all";

  return (
    <section className="relay-investigation-toolbar">
      <div className="relay-investigation-toolbar-search">
        <label htmlFor="relay-investigation-search">
          Search investigations
        </label>

        <div className="relay-investigation-search-field">
          <span aria-hidden="true">⌕</span>

          <input
            id="relay-investigation-search"
            type="search"
            value={searchQuery}
            placeholder="Search titles, assets, agents, or status"
            onChange={(event) =>
              onSearchChange(event.target.value)
            }
          />
        </div>
      </div>

      <div className="relay-investigation-toolbar-controls">
        <label>
          <span>Status</span>

          <select
            value={status}
            onChange={(event) =>
              onStatusChange(
                event.target.value as
                  | InvestigationStatus
                  | "all",
              )
            }
          >
            <option value="all">All statuses</option>

            {STATUS_OPTIONS.map((option) => (
              <option
                key={option}
                value={option}
              >
                {formatLabel(option)}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Priority</span>

          <select
            value={priority}
            onChange={(event) =>
              onPriorityChange(
                event.target.value as
                  | InvestigationPriority
                  | "all",
              )
            }
          >
            <option value="all">
              All priorities
            </option>
            <option value="high">High</option>
            <option value="medium">
              Medium
            </option>
            <option value="low">Low</option>
          </select>
        </label>
      </div>

      <footer className="relay-investigation-toolbar-footer">
        <span>
          {resultCount}{" "}
          {resultCount === 1
            ? "investigation"
            : "investigations"}
        </span>

        {hasActiveFilters && (
          <button
            className="relay-text-button"
            type="button"
            onClick={onClear}
          >
            Clear filters
          </button>
        )}
      </footer>
    </section>
  );
}