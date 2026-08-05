interface MemoryLibraryToolbarProps {
  searchQuery: string;
  incidentType: string;
  sortOrder: "newest" | "confidence" | "most_reused";
  incidentTypes: string[];
  resultCount: number;
  onSearchChange: (value: string) => void;
  onIncidentTypeChange: (value: string) => void;
  onSortOrderChange: (
    value: "newest" | "confidence" | "most_reused",
  ) => void;
  onClear: () => void;
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function MemoryLibraryToolbar({
  searchQuery,
  incidentType,
  sortOrder,
  incidentTypes,
  resultCount,
  onSearchChange,
  onIncidentTypeChange,
  onSortOrderChange,
  onClear,
}: MemoryLibraryToolbarProps) {
  const hasActiveFilters =
    searchQuery.trim().length > 0 ||
    incidentType !== "all" ||
    sortOrder !== "newest";

  return (
    <section className="relay-memory-toolbar">
      <div className="relay-memory-toolbar-search">
        <label htmlFor="relay-memory-search">
          Search organizational memory
        </label>

        <div className="relay-memory-search-field">
          <span aria-hidden="true">⌕</span>

          <input
            id="relay-memory-search"
            type="search"
            value={searchQuery}
            placeholder="Search root causes, resolutions, assets, or keywords"
            onChange={(event) =>
              onSearchChange(event.target.value)
            }
          />
        </div>
      </div>

      <div className="relay-memory-toolbar-controls">
        <label>
          <span>Incident type</span>

          <select
            value={incidentType}
            onChange={(event) =>
              onIncidentTypeChange(event.target.value)
            }
          >
            <option value="all">All incident types</option>

            {incidentTypes.map((type) => (
              <option key={type} value={type}>
                {formatLabel(type)}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Sort memories</span>

          <select
            value={sortOrder}
            onChange={(event) =>
              onSortOrderChange(
                event.target.value as
                  | "newest"
                  | "confidence"
                  | "most_reused",
              )
            }
          >
            <option value="newest">Newest first</option>
            <option value="confidence">
              Highest confidence
            </option>
            <option value="most_reused">
              Most reused
            </option>
          </select>
        </label>
      </div>

      <footer className="relay-memory-toolbar-footer">
        <span>
          {resultCount} verified{" "}
          {resultCount === 1 ? "memory" : "memories"}
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