import {
  useCallback,
  useEffect,
  useState,
} from "react";

interface SystemStatusProps {
  apiBaseUrl?: string;
}

interface HealthResponse {
  status?: string;
  service?: string;
  version?: string;
  datahub?: string;
  [key: string]: unknown;
}

type ConnectionState =
  | "checking"
  | "connected"
  | "degraded"
  | "offline";

const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api/v1";

function resolveConnectionState(
  response: HealthResponse,
): ConnectionState {
  const status = String(
    response.status ?? "",
  ).toLowerCase();

  if (
    status === "ok" ||
    status === "healthy" ||
    status === "ready"
  ) {
    return "connected";
  }

  return "degraded";
}

export default function SystemStatus({
  apiBaseUrl = DEFAULT_API_BASE_URL,
}: SystemStatusProps) {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("checking");

  const [health, setHealth] =
    useState<HealthResponse | null>(null);

  const checkHealth = useCallback(async () => {
    setConnectionState("checking");

    try {
      const response = await fetch(
        `${apiBaseUrl}/health`,
        {
          headers: {
            Accept: "application/json",
          },
        },
      );

      if (!response.ok) {
        setConnectionState("degraded");
        setHealth(null);
        return;
      }

      const payload =
        (await response.json()) as HealthResponse;

      setHealth(payload);
      setConnectionState(
        resolveConnectionState(payload),
      );
    } catch {
      setHealth(null);
      setConnectionState("offline");
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    void checkHealth();

    const intervalId = window.setInterval(
      () => {
        void checkHealth();
      },
      30000,
    );

    return () => {
      window.clearInterval(intervalId);
    };
  }, [checkHealth]);

  const title =
    connectionState === "connected"
      ? "Relay backend connected"
      : connectionState === "checking"
        ? "Checking Relay services"
        : connectionState === "degraded"
          ? "Relay service degraded"
          : "Relay backend offline";

  const description =
    connectionState === "connected"
      ? health?.datahub
        ? `DataHub: ${String(health.datahub)}`
        : "API and DataHub gateway available"
      : connectionState === "checking"
        ? "Verifying API availability"
        : connectionState === "degraded"
          ? "The API responded, but health checks did not pass"
          : "Start the FastAPI backend to reconnect";

  return (
    <button
      className={`relay-system-status is-${connectionState}`}
      type="button"
      title="Click to check the backend again"
      onClick={() => void checkHealth()}
    >
      <span className="relay-system-status-dot" />

      <span>
        <strong>{title}</strong>
        <small>{description}</small>
      </span>
    </button>
  );
}