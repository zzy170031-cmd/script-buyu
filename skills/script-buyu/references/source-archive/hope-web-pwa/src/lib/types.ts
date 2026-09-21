export type TransportCapability = "browser_direct" | "proxy_required" | "unsupported";
export type ProviderStatus = "ready" | "missing_config" | "failed" | "unsupported";
export type OperationMode = "expand_story" | "rewrite_story";

export const KB_ACTIONS = [
  "import_source",
  "expand_story",
  "rewrite_story",
  "accept_story_body",
  "create_story_task",
  "generate_storyboard",
  "repair_storyboard",
  "validate_result",
  "export_result",
  "golden_sample_review",
] as const;

export type KbAction = (typeof KB_ACTIONS)[number];
export type KbRuleGroup = "writing_group" | "director_group" | "validation_group";
export type KbActionState = "ready" | "passed" | "blocked" | "not_run";
export type ExportStatus = "not_ready" | "blocked" | "ready" | "exported";

export interface ProviderDefinition {
  providerId: string;
  displayName: string;
  transportCapability: TransportCapability;
  defaultBaseUrl: string;
  endpoint: string;
  defaultModels: string[];
  statusHint: string;
}

export interface ProviderModelRecord {
  provider_id: string;
  model_id: string;
  display_name: string;
  base_url_host: string;
  endpoint: string;
  transport_capability: TransportCapability;
  cors_check_result: string;
  last_connection_test: string | null;
  status: ProviderStatus;
}

export interface ProviderFormState {
  providerId: string;
  baseUrl: string;
  endpoint: string;
  apiKey: string;
  model: string;
  writingModel: string;
  directorModel: string;
  validatorModel: string;
  persistApiKey: boolean;
  connectionStatus: ProviderStatus;
  connectionMessage: string;
  corsCheckResult: string;
  lastConnectionTest: string | null;
}

export interface SourceFacts {
  characters: string[];
  locations: string[];
  events: string[];
  constraints: string[];
  visibleObjects: string[];
  beats: string[];
}

export interface RulePack {
  id: string;
  name: string;
  intent: string;
  influenceAxes: string[];
  directives: string[];
  negativeConstraints: string[];
}

export interface DurationCapacityProfile {
  duration: number;
  targetShotCount: number;
  beatDensity: string;
  pacingDirective: string;
}

export interface KbActionResult {
  action: KbAction;
  primary_group: KbRuleGroup;
  secondary_groups: KbRuleGroup[];
  state: KbActionState;
  summary: string;
  blocked_reason: string;
  influence_axes: string[];
  kb_oracle_affects_structure: boolean;
}

export type SemanticRole = "setup" | "action" | "reaction" | "turning_point" | "transition" | "hold" | "payoff";

export interface SemanticBeat {
  beat_id: string;
  order_index: number;
  source_text_summary: string;
  source_text_full?: string;
  source_span_ref: string;
  semantic_role: SemanticRole;
  scene_family: string;
  characters: string[];
  location_hint: string;
  action_intensity: number;
  dialogue_density: number;
  visual_complexity: number;
  continuity_priority: number;
  min_seconds: number;
  max_seconds: number;
  weight: number;
}

export interface BeatAllocation {
  beat_id: string;
  row_index: number;
  allocated_duration_seconds: number;
  reason: string;
  locked_by_user: boolean;
}

export interface DurationAllocationPlan {
  target_duration_seconds: number;
  scene_type_id: string;
  scene_family: string;
  strategy: "semantic_weighted_exact_sum";
  beats: SemanticBeat[];
  allocations: BeatAllocation[];
  total_seconds: number;
  duration_plan_hash: string;
  duration_plan_summary: string;
  warnings: string[];
}

export interface ShotTaskPlanCandidate {
  candidate_id: string;
  candidate_name: string;
  candidate_mode: "alternative_candidate" | "segmented_candidate";
  coverage_summary: string;
  script_fragment?: string;
  source_span_ref: string;
  semantic_beat_ids: string[];
  scene_group_id: string;
  scene_continuity_key: string;
  allocated_duration_seconds: number;
  estimated_row_count: number;
  director_reason_summary: string;
  same_scene_merge_reason_summary: string;
  prompt_guidance_summary: string;
}

export interface DirectorShotTaskPlan {
  plan_id: string;
  accepted_body_hash: string;
  scene_type_id: string;
  target_duration_seconds: number;
  kb_snapshot_hash: string;
  director_group_rule_pack_ids: string[];
  semantic_beats: SemanticBeat[];
  shot_task_candidates: ShotTaskPlanCandidate[];
  duration_allocation_plan: DurationAllocationPlan;
  prompt_guidance_summary: string;
  split_reason_summary: string;
  kb_oracle_affects_structure: true;
}

export interface StoryboardTask {
  task_id: string;
  task_hash: string;
  storyboard_task_hash: string;
  task_name: string;
  task_index: number;
  task_source_kind: "system_candidate" | "full_narrative" | "confirmed_body" | "custom_fragment" | "segmented_queue";
  task_source_label: string;
  people_summary: string;
  script_fragment: string;
  original_fragment: string;
  queue_status: "pending" | "generated";
  current_body_source: "accepted_body";
  accepted_body_hash: string;
  scene_type_id: string;
  scene_type_label: string;
  target_duration_seconds: number;
  kb_snapshot_hash: string;
  selected_sample_ids: string[];
  selected_kb_rules: string[];
  writing_group_rule_pack_ids: string[];
  director_group_rule_pack_ids: string[];
  validation_group_rule_pack_ids: string[];
  output_intent: "storyboard_rows";
  source_lineage: "accepted_body";
  generation_group: string;
  estimated_shot_count: number;
  task_queue: StoryboardTaskQueueItem[];
  director_plan: DirectorShotTaskPlan;
  duration_allocation_plan: DurationAllocationPlan;
  duration_allocation_strategy: string;
  continuity_status: string;
  created_from_confirmed_body: boolean;
  preserve_previous_task: boolean;
  rows_hash: string;
  confirmed_row_hash: string;
  stale_state: boolean;
  sync_status: "fresh" | "stale";
  stale_reasons: string[];
  created_at: string;
}

export interface StoryboardTaskQueueItem {
  candidate_id: string;
  title: string;
  candidate_mode: "alternative_candidate" | "segmented_candidate";
  source_kind: "system_candidate" | "full_narrative" | "confirmed_body" | "custom_fragment";
  source_label: string;
  people_summary: string;
  script_fragment: string;
  original_fragment: string;
  coverage_summary: string;
  source_span_ref: string;
  semantic_beat_ids: string[];
  scene_group_id: string;
  scene_continuity_key: string;
  allocated_duration_seconds: number;
  estimated_row_count: number;
  director_reason_summary: string;
  same_scene_merge_reason_summary: string;
  prompt_guidance_summary: string;
  order_index: number;
}

export interface KbSnapshot {
  snapshotVersion: string;
  sceneTypes: string[];
  allowedDurations: number[];
  writingRulePacks: RulePack[];
  directorRulePacks: RulePack[];
  validationRulePacks: RulePack[];
  sceneMappings: Record<
    string,
    {
      writingRulePackIds: string[];
      directorRulePackIds: string[];
      validationRulePackIds: string[];
      sceneProfile: string;
      negativeConstraints: string[];
      influenceAxes: string[];
    }
  >;
  durationProfiles: DurationCapacityProfile[];
}

export interface SanitizedKbSummary {
  [key: string]: unknown;
  kb_snapshot_hash: string;
  scene_type_count: number;
  scene_type_id: string;
  scene_type_label: string;
  duration_options: number[];
  selected_sample_ids: string[];
  selected_kb_rules: string[];
  writing_group_rule_pack_ids: string[];
  director_group_rule_pack_ids: string[];
  validation_group_rule_pack_ids: string[];
  kb_context_summary: string;
  applied_to: KbAction[];
  action_results: KbActionResult[];
  influence_axes: string[];
  scene_profile: string;
  negative_constraints: string[];
  kb_oracle_affects_structure: boolean;
  raw_sample_text_absent: true;
  overlay_json_absent: true;
}

export interface NarrativeResult {
  body: string;
  title: string;
  sourceFacts: SourceFacts;
  validatorResult: ValidationResult;
  evidence: GenerationEvidence;
}

export interface StoryboardRow {
  shot_index: number;
  beat_id?: string;
  source_span_ref?: string;
  allocated_duration_seconds?: number;
  duration_reason?: string;
  person: string;
  shot_size: string;
  camera: string;
  visual_description: string;
  character_action: string;
  dialogue_or_narration: string;
  prompt_text: string;
  duration_seconds: number;
  status: string;
  note: string;
  is_user_edited?: boolean;
}

export interface StoryboardResult {
  rows: StoryboardRow[];
  validatorResult: ValidationResult;
  evidence: GenerationEvidence;
}

export interface ValidationIssue {
  code: string;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface ValidationResult {
  passed: boolean;
  summary: string;
  issues: ValidationIssue[];
}

export interface GenerationEvidence {
  [key: string]: unknown;
  artifact_identity: string;
  current_kb_action: KbAction;
  source_lineage: string;
  source_lineage_evidence: string;
  source_hash: string;
  output_intent: "narrative_body" | "storyboard_rows";
  story_fact_frame: string;
  accepted_body_hash: string;
  storyboard_task: string;
  storyboard_task_hash: string;
  kb_snapshot_hash: string;
  selected_sample_ids: string[];
  selected_kb_rules: string[];
  writing_group_rule_pack_ids: string[];
  director_group_rule_pack_ids: string[];
  validation_group_rule_pack_ids: string[];
  kb_context_summary: string;
  applied_to: KbAction[];
  kb_action_results: KbActionResult[];
  influence_axes: string[];
  kb_oracle_affects_structure: boolean;
  raw_sample_text_absent: true;
  overlay_json_absent: true;
  semantic_segmentation_evidence: {
    source_segment_ids: string[];
    semantic_beat_ids: string[];
    semantic_beat_summary: string;
    split_reason_summary: string;
    must_preserve_fact_summary: string;
    must_not_merge_reason_summary: string;
  };
  duration_allocation_evidence: {
    target_duration_seconds: number;
    duration_plan_hash: string;
    duration_plan_summary: string;
    allocated_row_duration_seconds: number[];
    duration_source: "semantic_beat_kb_weighted";
    duration_density_reason_summary: string;
    single_row_duration_cap_seconds: number;
    duration_overflow_or_compression_reason: string;
  };
  same_scene_grouping_evidence: {
    scene_group_id: string;
    same_scene_merge_applied: boolean;
    merged_shot_task_ids: string[];
    scene_continuity_key: string;
    merge_reason_summary: string;
    scene_change_boundary_reason: string;
    visual_state_delta_summary: string;
  };
  validation_evidence: {
    duration_sum_matches_target: boolean;
    single_row_duration_cap_passed: boolean;
    semantic_beat_preserved: boolean;
    same_scene_merge_safe: boolean;
    non_empty_rows_passed: boolean;
    no_pseudo_success: boolean;
    export_safety_passed: boolean;
  };
  scene_type_id: string;
  scene_type_label: string;
  scene_type_canonical_coverage: number;
  scene_type_valid: boolean;
  target_duration_seconds: number;
  rows_hash: string;
  confirmed_row_hash: string;
  export_source_hash: string;
  prompt_compilation_version: string;
  warning_taxonomy: string[];
  warning_taxonomy_classified: boolean;
  hardfail_warning_absent: boolean;
  stale_state: boolean;
  stale_task_detected: boolean;
  stale_rows_detected: boolean;
  task_sync_status: "fresh" | "stale";
  rows_count: number;
  rows_match: boolean;
  prompt_text_present: boolean;
  prompt_text_boundary_passed: boolean;
  prompt_text_not_summary_only: boolean;
  visual_description_visible_frame_passed: boolean;
  visual_description_no_trace: boolean;
  prompt_compiled_after_final_row: boolean;
  person_field_valid: boolean;
  location_not_in_person: boolean;
  action_fragment_not_in_person: boolean;
  scene_term_not_in_person: boolean;
  generic_role_placeholder_absent: boolean;
  validator_pseudo_success_detected: boolean;
  blocked_reason: string;
  fallback_used: boolean;
  provider_failover_used: boolean;
  local_candidate: boolean;
  row_prompt_visual_gate_evidence: string;
  field_aware_entity_gate_evidence: string;
  manual_edit_confirmed_row_evidence: string;
  blocked_warning_ui_evidence: string;
  human_review_spotcheck_evidence: string;
  export_evidence: string[];
  validator_result: ValidationResult;
  provider_id: string;
  model_id: string;
  base_url_host: string;
  cors_check_result: string;
  generated_at: string;
}

export interface GenerationContext {
  sourceText: string;
  sceneTypeId: string;
  sceneTypeLabel: string;
  targetDuration: number;
  mode: OperationMode;
  provider: ProviderFormState;
  kbSnapshot: KbSnapshot;
  kbSummary: SanitizedKbSummary;
}

export interface ModelResponse<T> {
  content: string;
  parsed: T;
  rawUsage?: unknown;
}

export interface ExportBundle {
  fileName: string;
  mimeType: string;
  content: string;
  kind: "storyboard" | "script";
  format: "excel";
}

export interface ExportAudit {
  file_name: string;
  format: "excel";
  kind: "storyboard" | "script";
  usable: boolean;
  contains_secret_leakage: boolean;
  contains_local_path: boolean;
  contains_raw_kb: boolean;
  contains_internal_refs: boolean;
  sampled_export_preview_present: boolean;
  duration_seconds: number;
  target_duration_seconds: number;
  preview: string[];
}

export interface QaTrace {
  [key: string]: unknown;
  provider_id: string;
  model_id: string;
  base_url_host: string;
  connection_status: ProviderStatus;
  connection_message: string;
  scene_type_id: string;
  scene_type_label: string;
  target_duration_seconds: number;
  accepted_body_ready: boolean;
  accepted_body_hash: string;
  storyboard_task_hash: string;
  storyboard_task_sync_status: "missing" | "fresh" | "stale";
  source_lineage: string;
  kb_ready: boolean;
  kb_adapter_source: "external" | "fallback";
  kb_snapshot_hash: string;
  kb_rule_pack_count: number;
  selected_sample_ids: string[];
  selected_kb_rules: string[];
  writing_group_rule_pack_ids: string[];
  director_group_rule_pack_ids: string[];
  validation_group_rule_pack_ids: string[];
  active_rule_pack_ids: string[];
  style_rule_pack_ids: string[];
  kb_context_summary: string;
  applied_to: KbAction[];
  kb_action_results: KbActionResult[];
  influence_axes: string[];
  style_influence_axes: string[];
  kb_oracle_affects_structure: boolean;
  raw_sample_text_absent: true;
  overlay_json_absent: true;
  candidate_duration_semantics: "" | "alternative_candidate" | "segmented_candidate";
  task_creation_candidate_count: number;
  queued_task_count: number;
  queued_task_duration_sum: number;
  queued_task_duration_remaining: number;
  current_task_allocated_duration_seconds: number;
  candidate_total_budget_multiplied: boolean;
  queued_task_duration_overflow: boolean;
  queued_task_duration_sum_mismatch: boolean;
  candidate_duration_semantics_missing: boolean;
  repeated_total_budget_tasks: boolean;
  director_plan_present: boolean;
  director_plan_from_accepted_body: boolean;
  director_rule_pack_present: boolean;
  director_split_reason_present: boolean;
  shot_task_candidate_raw_text_only: boolean;
  semantic_split_equal_by_text_length: boolean;
  semantic_split_equal_by_candidate_count: boolean;
  same_scene_merge_reason_present: boolean;
  row_generated_with_director_plan: boolean;
  prompt_generated_with_director_plan: boolean;
  duration_allocator_strategy: string;
  duration_plan_hash: string;
  duration_plan_summary: string;
  allocated_row_duration_seconds: number[];
  semantic_beat_ids: string[];
  semantic_beat_summary: string;
  duration_allocator_equal_split_without_reason: boolean;
  semantic_beat_content_mismatch: boolean;
  rows_count: number;
  rows_duration_sum: number;
  rows_match: boolean;
  prompt_text_present: boolean;
  prompt_text_boundary_passed: boolean;
  prompt_text_not_summary_only: boolean;
  visual_description_visible_frame_passed: boolean;
  visual_description_no_trace: boolean;
  prompt_compiled_after_final_row: boolean;
  repeated_total_budget_rows: boolean;
  confirmed_duration_seconds: number;
  confirmed_duration_mismatch: boolean;
  stale_task_detected: boolean;
  stale_rows_detected: boolean;
  person_field_valid: boolean;
  location_not_in_person: boolean;
  action_fragment_not_in_person: boolean;
  scene_term_not_in_person: boolean;
  generic_role_placeholder_absent: boolean;
  validator_pseudo_success_detected: boolean;
  warning_taxonomy_classified: boolean;
  warning_taxonomy: string[];
  hardfail_warning_absent: boolean;
  fallback_used: boolean;
  provider_failover_used: boolean;
  local_candidate: boolean;
  export_status: ExportStatus;
  export_duration_seconds: number;
  export_duration_mismatch: boolean;
  ui_internal_evidence_exposed: boolean;
  export_internal_evidence_exposed: boolean;
  export_audit: ExportAudit[];
}
