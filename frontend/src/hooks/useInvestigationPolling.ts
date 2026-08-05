import { useEffect } from "react";

type InvestigationStatus =
  | "draft"
  | "queued"
  | "gathering_context"
  | "investigating"
  | "repairing"
  | "reviewing"
  | "awaiting_approval"
  | "archiving";

interface Props {
  status: string;
  refresh: () => void | Promise<void>;
}

const ACTIVE_STATUSES: InvestigationStatus[] = [
  "queued",
  "gathering_context",
  "investigating",
  "repairing",
  "reviewing",
  "archiving",
];

export default function useInvestigationPolling({
  status,
  refresh,
}: Props) {
  useEffect(() => {
    if (
      !ACTIVE_STATUSES.includes(
        status as InvestigationStatus,
      )
    ) {
      return;
    }

    const interval = window.setInterval(() => {
      void refresh();
    }, 2000);

    return () => window.clearInterval(interval);
  }, [status, refresh]);
}