import { useMemo } from "react";

import type {
  LineageEdge,
  LineageNode,
} from "../types/api";

interface LineageGraphProps {
  nodes: LineageNode[];
  edges: LineageEdge[];
  rootUrn?: string;
}

interface DepthGroup {
  depth: number;
  label: string;
  nodes: LineageNode[];
}

function formatLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function getDepthLabel(depth: number): string {
  if (depth === 0) {
    return "Selected asset";
  }

  if (depth < 0) {
    return `Upstream ${Math.abs(depth)}`;
  }

  return `Downstream ${depth}`;
}

function getPlatformInitial(
  platform: string,
): string {
  const normalized = platform.trim();

  if (!normalized) {
    return "?";
  }

  return normalized.slice(0, 1).toUpperCase();
}

export default function LineageGraph({
  nodes,
  edges,
  rootUrn,
}: LineageGraphProps) {
  const groups = useMemo<DepthGroup[]>(() => {
    const grouped = new Map<
      number,
      LineageNode[]
    >();

    nodes.forEach((node) => {
      const existing =
        grouped.get(node.depth) ?? [];

      existing.push(node);
      grouped.set(node.depth, existing);
    });

    return Array.from(grouped.entries())
      .sort(
        ([leftDepth], [rightDepth]) =>
          leftDepth - rightDepth,
      )
      .map(([depth, groupedNodes]) => ({
        depth,
        label: getDepthLabel(depth),
        nodes: groupedNodes.sort((left, right) =>
          left.label.localeCompare(
            right.label,
          ),
        ),
      }));
  }, [nodes]);

  const connectionCountByUrn = useMemo(() => {
    const counts = new Map<string, number>();

    edges.forEach((edge) => {
      counts.set(
        edge.source,
        (counts.get(edge.source) ?? 0) + 1,
      );

      counts.set(
        edge.target,
        (counts.get(edge.target) ?? 0) + 1,
      );
    });

    return counts;
  }, [edges]);

  if (nodes.length === 0) {
    return (
      <div className="relay-empty-state">
        DataHub lineage has not been loaded yet.
      </div>
    );
  }

  return (
    <div className="relay-lineage-graph">
      <header className="relay-lineage-graph-summary">
        <div>
          <span>Assets</span>
          <strong>{nodes.length}</strong>
        </div>

        <div>
          <span>Dependencies</span>
          <strong>{edges.length}</strong>
        </div>

        <div>
          <span>Maximum depth</span>
          <strong>
            {Math.max(
              ...nodes.map((node) =>
                Math.abs(node.depth),
              ),
            )}
          </strong>
        </div>
      </header>

      <div className="relay-lineage-columns">
        {groups.map((group, groupIndex) => (
          <section
            className="relay-lineage-column"
            key={group.depth}
          >
            <header>
              <span>{group.label}</span>

              <small>
                {group.nodes.length}{" "}
                {group.nodes.length === 1
                  ? "asset"
                  : "assets"}
              </small>
            </header>

            <div className="relay-lineage-column-nodes">
              {group.nodes.map((node) => {
                const isRoot =
                  node.urn === rootUrn ||
                  node.depth === 0;

                const connectionCount =
                  connectionCountByUrn.get(
                    node.urn,
                  ) ?? 0;

                return (
                  <article
                    className={[
                      "relay-lineage-graph-node",
                      isRoot
                        ? "is-root"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    key={node.id}
                  >
                    <div className="relay-lineage-platform-mark">
                      {getPlatformInitial(
                        node.platform,
                      )}
                    </div>

                    <div className="relay-lineage-graph-node-copy">
                      <strong>
                        {node.label}
                      </strong>

                      <span>
                        {formatLabel(
                          node.entity_type,
                        )}
                      </span>

                      <small>
                        {node.platform} ·{" "}
                        {connectionCount}{" "}
                        {connectionCount === 1
                          ? "connection"
                          : "connections"}
                      </small>
                    </div>

                    {isRoot && (
                      <span className="relay-lineage-root-badge">
                        Selected
                      </span>
                    )}

                    <details>
                      <summary>
                        View asset URN
                      </summary>

                      <code>{node.urn}</code>
                    </details>
                  </article>
                );
              })}
            </div>

            {groupIndex <
              groups.length - 1 && (
              <div
                className="relay-lineage-column-connector"
                aria-hidden="true"
              >
                <span>→</span>
              </div>
            )}
          </section>
        ))}
      </div>

      <footer className="relay-lineage-legend">
        <span>
          <i className="is-selected" />
          Selected asset
        </span>

        <span>
          <i className="is-related" />
          Related DataHub asset
        </span>

        <span>
          Direction follows dependency flow toward
          the selected asset.
        </span>
      </footer>
    </div>
  );
}