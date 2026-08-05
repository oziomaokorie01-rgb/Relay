export type InvestigationPriority = "low" | "medium" | "high";

export type InvestigationStatus =
  | "draft"
  | "queued"
  | "gathering_context"
  | "investigating"
  | "repairing"
  | "reviewing"
  | "awaiting_approval"
  | "archiving"
  | "completed"
  | "failed"
  | "cancelled";

export type AgentName =
  | "system"
  | "investigator"
  | "repair"
  | "reviewer"
  | "archivist"
  | "human";

export type ActivityStatus =
  | "queued"
  | "started"
  | "in_progress"
  | "completed"
  | "warning"
  | "failed"
  | "cancelled";

export type EvidenceType =
  | "schema_change"
  | "lineage_dependency"
  | "freshness_failure"
  | "quality_failure"
  | "ownership_signal"
  | "governance_rule"
  | "previous_memory"
  | "query_result"
  | "documentation"
  | "manual_context";

export type RepairArtifactType =
  | "sql"
  | "dbt_model"
  | "data_quality_test"
  | "configuration"
  | "pipeline_patch"
  | "documentation"
  | "runbook"
  | "recommendation_only";

export type RepairRiskLevel = "low" | "medium" | "high";

export type RepairProposalStatus =
  | "draft"
  | "proposed"
  | "under_review"
  | "approved"
  | "needs_revision"
  | "rejected";

export type ReviewDecision =
  | "approved"
  | "approved_with_conditions"
  | "needs_revision"
  | "rejected";

export type MemoryVerificationStatus =
  | "draft"
  | "under_review"
  | "verified"
  | "superseded"
  | "archived"
  | "rejected";

export type MemoryReuseType =
  | "root_cause_precedent"
  | "repair_precedent"
  | "test_precedent"
  | "related_incident"
  | "general_context";

export interface InvestigationCreateInput {
  title: string;
  description: string;
  asset_urn: string;
  priority: InvestigationPriority;
}

export interface InvestigationCreated {
  id: string;
  status: InvestigationStatus;
}

export interface InvestigationSummary {
  id: string;
  title: string;
  asset_urn: string;
  priority: InvestigationPriority;
  status: InvestigationStatus;
  current_agent: string | null;
  overall_confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface AssetOwner {
  name: string;
  type: string;
  email: string | null;
}

export interface AssetReference {
  urn: string;
  name: string;
  display_name: string;
  entity_type: string;
  platform: string;
}

export interface AssetContext {
  urn: string;
  name: string;
  display_name: string;
  entity_type: string;
  platform: string;
  domain: string | null;
  description: string | null;
  owners: AssetOwner[];
  tags: string[];
  schema_fields: unknown[];
  upstream_assets: AssetReference[];
  downstream_assets: AssetReference[];
  last_updated: string | null;
  quality_status: string | null;
  memory_count: number;
  metadata: Record<string, unknown>;
}

export interface LineageNode {
  id: string;
  urn: string;
  label: string;
  entity_type: string;
  platform: string;
  depth: number;
}

export interface LineageEdge {
  source: string;
  target: string;
  direction: string;
}

export interface LineageGraph {
  root_urn: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export interface InvestigationContextSnapshot {
  asset?: AssetContext;
  lineage?: LineageGraph;
  summary?: Record<string, unknown>;
}

export interface InvestigationDetail extends InvestigationSummary {
  description: string;
  context_snapshot: InvestigationContextSnapshot;
  root_cause_summary: string | null;
  failure_message: string | null;
  completed_at: string | null;
}

export interface AgentActivity {
  id: string;
  investigation_id: string;
  agent_name: AgentName;
  event_type: string;
  status: ActivityStatus;
  message: string;
  structured_payload: Record<string, unknown>;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface Evidence {
  id: string;
  investigation_id: string;
  type: EvidenceType;
  title: string;
  description: string;
  source_asset_urn: string | null;
  source_reference: string | null;
  confidence: number;
  payload: Record<string, unknown>;
  created_by_agent: string;
  created_at: string;
}

export interface RepairProposal {
  id: string;
  investigation_id: string;
  summary: string;
  artifact_type: RepairArtifactType;
  artifact_content: string | null;
  language: string | null;
  risk_level: RepairRiskLevel;
  expected_outcome: string;
  rollback_plan: string | null;
  affected_asset_urns: string[];
  tests: Array<Record<string, unknown>>;
  assumptions: string[];
  evidence_ids: string[];
  confidence: number;
  status: RepairProposalStatus;
  created_at: string;
}

export interface ReviewCheck {
  status: "pass" | "warning" | "fail";
  explanation: string;
}

export interface Review {
  id: string;
  investigation_id: string;
  repair_proposal_id: string;
  decision: ReviewDecision;
  evidence_coverage: ReviewCheck;
  schema_compatibility: ReviewCheck;
  downstream_risk: ReviewCheck;
  governance_compliance: ReviewCheck;
  confidence: number;
  conditions: string[];
  missing_evidence: string[];
  notes: string | null;
  created_at: string;
}

export interface HumanApprovalInput {
  decision: "approve" | "request_revision" | "reject";
  edited_title: string | null;
  edited_summary: string | null;
  notes: string | null;
}

export interface HumanApprovalResponse {
  investigation_id: string;
  decision: HumanApprovalInput["decision"];
  status: InvestigationStatus;
  message: string;
}

export interface RelayMemory {
  id: string;
  memory_key: string;
  version: number;
  originating_investigation_id: string;
  primary_asset_urn: string;
  title: string;
  summary: string;
  incident_type: string;
  root_cause: string;
  resolution: string;
  confidence: number;
  verification_status: MemoryVerificationStatus;
  keywords: string[];
  related_asset_urns: string[];
  evidence_ids: string[];
  supersedes_memory_id: string | null;
  created_at: string;
  updated_at: string;
  verified_at: string | null;
}

export interface InvestigationArchiveResponse {
  investigation_id: string;
  investigation_status: InvestigationStatus;
  memory: RelayMemory;
}

export interface MemoryReuseEvent {
  id: string;
  memory_id: string;
  investigation_id: string;
  similarity_score: number | null;
  reuse_type: MemoryReuseType;
  agent_explanation: string;
  accepted: boolean;
  estimated_steps_skipped: number;
  estimated_time_saved_minutes: number;
  created_at: string;
}