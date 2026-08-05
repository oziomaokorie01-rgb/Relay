import type {
  AgentActivity,
  Evidence,
AssetReference,
  HumanApprovalInput,
  HumanApprovalResponse,
  InvestigationArchiveResponse,
  InvestigationCreateInput,
  InvestigationCreated,
  InvestigationDetail,
  InvestigationSummary,
  MemoryReuseEvent,
  RelayMemory,
  RepairProposal,
  Review,
} from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api/v1";

class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(
    message: string,
    status: number,
    detail: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new ApiError(
      "Could not connect to the Relay backend.",
      0,
      error,
    );
  }

  const contentType = response.headers.get("content-type") ?? "";

  let payload: unknown = null;

  if (contentType.includes("application/json")) {
    payload = await response.json();
  } else {
    const text = await response.text();
    payload = text || null;
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload
        ? (payload as { detail: unknown }).detail
        : payload;

    const message =
      typeof detail === "string"
        ? detail
        : `Relay request failed with status ${response.status}.`;

    throw new ApiError(
      message,
      response.status,
      detail,
    );
  }

  return payload as T;
}

function encodePathValue(value: string): string {
  return encodeURIComponent(value.trim());
}
export function searchAssets(
  query: string,
  limit = 10,
): Promise<AssetReference[]> {
  const normalizedQuery = query.trim();

  if (!normalizedQuery) {
    return Promise.resolve([]);
  }

  const params = new URLSearchParams({
    q: normalizedQuery,
    limit: String(limit),
  });

  return request<AssetReference[]>(
    `/assets/search?${params.toString()}`,
  );
}
export function createInvestigation(
  input: InvestigationCreateInput,
): Promise<InvestigationCreated> {
  return request<InvestigationCreated>("/investigations", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listInvestigations(
  limit = 50,
  offset = 0,
): Promise<InvestigationSummary[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  return request<InvestigationSummary[]>(
    `/investigations?${params.toString()}`,
  );
}

export function getInvestigation(
  investigationId: string,
): Promise<InvestigationDetail> {
  return request<InvestigationDetail>(
    `/investigations/${encodePathValue(investigationId)}`,
  );
}

export function runInvestigation(
  investigationId: string,
): Promise<InvestigationDetail> {
  return request<InvestigationDetail>(
    `/investigations/${encodePathValue(investigationId)}/run`,
    {
      method: "POST",
    },
  );
}

export function getInvestigationActivity(
  investigationId: string,
): Promise<AgentActivity[]> {
  return request<AgentActivity[]>(
    `/investigations/${encodePathValue(investigationId)}/activity`,
  );
}

export function getInvestigationEvidence(
  investigationId: string,
): Promise<Evidence[]> {
  return request<Evidence[]>(
    `/investigations/${encodePathValue(investigationId)}/evidence`,
  );
}

export function getInvestigationRepair(
  investigationId: string,
): Promise<RepairProposal> {
  return request<RepairProposal>(
    `/investigations/${encodePathValue(investigationId)}/repair`,
  );
}

export function getInvestigationReview(
  investigationId: string,
): Promise<Review> {
  return request<Review>(
    `/investigations/${encodePathValue(investigationId)}/review`,
  );
}

export function submitInvestigationApproval(
  investigationId: string,
  input: HumanApprovalInput,
): Promise<HumanApprovalResponse> {
  return request<HumanApprovalResponse>(
    `/investigations/${encodePathValue(investigationId)}/approval`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export function archiveInvestigation(
  investigationId: string,
): Promise<InvestigationArchiveResponse> {
  return request<InvestigationArchiveResponse>(
    `/investigations/${encodePathValue(investigationId)}/archive`,
    {
      method: "POST",
    },
  );
}

export function getInvestigationMemoryReuse(
  investigationId: string,
): Promise<MemoryReuseEvent[]> {
  return request<MemoryReuseEvent[]>(
    `/investigations/${encodePathValue(investigationId)}/memory-reuse`,
  );
}

export function listMemories(
  options: {
    query?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<RelayMemory[]> {
  const params = new URLSearchParams();

  if (options.query?.trim()) {
    params.set("q", options.query.trim());
  }

  params.set("limit", String(options.limit ?? 50));
  params.set("offset", String(options.offset ?? 0));

  return request<RelayMemory[]>(
    `/memories?${params.toString()}`,
  );
}

export function getMemory(
  memoryId: string,
): Promise<RelayMemory> {
  return request<RelayMemory>(
    `/memories/${encodePathValue(memoryId)}`,
  );
}

export function getMemoryReuseHistory(
  memoryId: string,
): Promise<MemoryReuseEvent[]> {
  return request<MemoryReuseEvent[]>(
    `/memories/${encodePathValue(memoryId)}/reuse`,
  );
}

export { ApiError };