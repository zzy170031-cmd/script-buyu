import { KB_SNAPSHOT } from "./kb";
import {
  buildAssignmentSignalPattern,
  buildExactFieldPattern,
  CORE_INTERNAL_SOURCE_FIELD_NAMES,
  INTERNAL_FIELD_NAMES,
  REQUIRED_DENIED_SAFETY_CATEGORIES,
} from "./safetyFields";
import type { KbSnapshot, RulePack } from "./types";

export interface PwaKbAdapterOutput {
  adapter_version: "pwa-kb-adapter/v0.2";
  adapter_status: "prototype" | "candidate" | "verified" | "activated";
  source_snapshot_version: string;
  source_snapshot_hash: string;
  scene_catalog_status: "partial" | "full";
  rule_pack_crosswalk_status: "prototype" | "verified" | "not_required";
  pwa_snapshot: KbSnapshot;
  sanitized_summary_contract: {
    summary_only: true;
    allowed_fields: string[];
    denied_fields: string[];
  };
  fail_closed: {
    fallback_required: true;
    fallback_target: string;
    reject_when: string[];
  };
}

export interface CompileAdapterOptions {
  allowPrototype?: boolean;
  allowPartialSceneCatalog?: boolean;
}

export interface CompileAdapterResult {
  accepted: boolean;
  snapshot?: KbSnapshot;
  rejectReason?: string;
}

export interface LoadAdapterOptions extends CompileAdapterOptions {
  url?: string;
  fetcher?: typeof fetch;
  fallbackSnapshot?: KbSnapshot;
}

export interface LoadAdapterResult {
  snapshot: KbSnapshot;
  source: "external" | "fallback";
  rejectReason?: string;
}

const ADAPTER_VERSION = "pwa-kb-adapter/v0.2";
const HASH_PATTERN = /^sha256:[A-Za-z0-9._-]+$/;
const ADAPTER_STATUSES = ["prototype", "candidate", "verified", "activated"] as const;
const SCENE_CATALOG_STATUSES = ["partial", "full"] as const;
const RULE_PACK_CROSSWALK_STATUSES = ["prototype", "verified", "not_required"] as const;
const ADAPTER_OUTPUT_KEYS = [
  "adapter_version",
  "adapter_status",
  "source_snapshot_version",
  "source_snapshot_hash",
  "scene_catalog_status",
  "rule_pack_crosswalk_status",
  "pwa_snapshot",
  "sanitized_summary_contract",
  "fail_closed",
] as const;
const SNAPSHOT_KEYS = [
  "snapshotVersion",
  "sceneTypes",
  "allowedDurations",
  "writingRulePacks",
  "directorRulePacks",
  "validationRulePacks",
  "sceneMappings",
  "durationProfiles",
] as const;
const RULE_PACK_KEYS = ["id", "name", "intent", "influenceAxes", "directives", "negativeConstraints"] as const;
const SCENE_MAPPING_KEYS = [
  "writingRulePackIds",
  "directorRulePackIds",
  "validationRulePackIds",
  "sceneProfile",
  "negativeConstraints",
  "influenceAxes",
] as const;
const DURATION_PROFILE_KEYS = ["duration", "targetShotCount", "beatDensity", "pacingDirective"] as const;
const SUMMARY_CONTRACT_KEYS = ["summary_only", "allowed_fields", "denied_fields"] as const;
const FAIL_CLOSED_KEYS = ["fallback_required", "fallback_target", "reject_when"] as const;
const REQUIRED_REJECT_REASONS = [
  "missing_or_unparseable",
  "unresolved_rule_pack_reference",
] as const;
const RAW_OR_CREDENTIAL_REJECT_REASONS = ["raw_or_secret_field_present", "credential_or_raw_field_present"] as const;
const ABSTRACT_CREDENTIAL_MATERIAL_CATEGORY = "credential_material";
const ABSTRACT_LOCAL_ONLY_IDENTIFIER_CATEGORY = "local_only_identifier";
const BASE_REQUIRED_DENIED_SAFETY_CATEGORIES = REQUIRED_DENIED_SAFETY_CATEGORIES.filter(
  (field) =>
    field !== INTERNAL_FIELD_NAMES.apiKey &&
    field !== "token" &&
    field !== "secret" &&
    field !== INTERNAL_FIELD_NAMES.localEnvironmentPath,
);
const LEGACY_CREDENTIAL_DENIED_SAFETY_CATEGORIES = [INTERNAL_FIELD_NAMES.apiKey, "token", "secret"] as const;
const ALL_DENIED_SUMMARY_CATEGORIES = [
  ...REQUIRED_DENIED_SAFETY_CATEGORIES,
  ABSTRACT_CREDENTIAL_MATERIAL_CATEGORY,
  ABSTRACT_LOCAL_ONLY_IDENTIFIER_CATEGORY,
] as const;
const RAW_FIELD_PATTERN = buildExactFieldPattern([
  ...CORE_INTERNAL_SOURCE_FIELD_NAMES,
  INTERNAL_FIELD_NAMES.rawGraph,
  INTERNAL_FIELD_NAMES.overlayJson,
  INTERNAL_FIELD_NAMES.internalSourceMaterial,
  INTERNAL_FIELD_NAMES.internalKbContent,
  INTERNAL_FIELD_NAMES.internalGraphPayload,
  INTERNAL_FIELD_NAMES.auditGovernanceMetadata,
  INTERNAL_FIELD_NAMES.overlayPayload,
  INTERNAL_FIELD_NAMES.promptConstructionMiddleware,
  INTERNAL_FIELD_NAMES.providerConfig,
  INTERNAL_FIELD_NAMES.apiKey,
  "token",
  "secret",
  INTERNAL_FIELD_NAMES.localPath,
  INTERNAL_FIELD_NAMES.localEnvironmentPath,
]);
const RAW_VALUE_PATTERN = buildAssignmentSignalPattern([
  INTERNAL_FIELD_NAMES.sourceRegister,
  INTERNAL_FIELD_NAMES.sourceRefs,
  INTERNAL_FIELD_NAMES.sourceUrl,
  INTERNAL_FIELD_NAMES.sourceTitle,
  INTERNAL_FIELD_NAMES.sourceCandidateRefs,
  INTERNAL_FIELD_NAMES.promptBody,
  INTERNAL_FIELD_NAMES.overlayJson,
  INTERNAL_FIELD_NAMES.rawKbRows,
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function hasString(value: Record<string, unknown>, key: string): boolean {
  return typeof value[key] === "string" && String(value[key]).length > 0;
}

function hasStringArray(value: Record<string, unknown>, key: string): boolean {
  return Array.isArray(value[key]) && (value[key] as unknown[]).every((item) => typeof item === "string");
}

function hasNumberArray(value: Record<string, unknown>, key: string): boolean {
  return (
    Array.isArray(value[key]) &&
    (value[key] as unknown[]).length > 0 &&
    (value[key] as unknown[]).every((item) => Number.isInteger(item) && Number(item) > 0)
  );
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const allowed = new Set(keys);
  return Object.keys(value).every((key) => allowed.has(key)) && keys.every((key) => key in value);
}

function hasUniqueItems(value: readonly unknown[]): boolean {
  return new Set(value).size === value.length;
}

function isOneOf<T extends readonly string[]>(value: unknown, values: T): value is T[number] {
  return typeof value === "string" && values.includes(value);
}

function isMetadataStringList(path: readonly string[]): boolean {
  const joined = path.join(".");
  return (
    joined === "sanitized_summary_contract.allowed_fields" ||
    joined === "sanitized_summary_contract.denied_fields" ||
    joined === "fail_closed.reject_when"
  );
}

function containsDeniedRawSignal(value: unknown, path: readonly string[] = []): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => containsDeniedRawSignal(item, path));
  }
  if (typeof value === "string") {
    return !isMetadataStringList(path) && RAW_VALUE_PATTERN.test(value);
  }
  if (!isRecord(value)) {
    return false;
  }
  return Object.entries(value).some(
    ([key, item]) => RAW_FIELD_PATTERN.test(key) || containsDeniedRawSignal(item, [...path, key]),
  );
}

function validateSummaryContract(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, SUMMARY_CONTRACT_KEYS)) return false;
  if (value.summary_only !== true) return false;
  if (!hasStringArray(value, "allowed_fields") || !hasStringArray(value, "denied_fields")) return false;
  const allowedFields = new Set((value.allowed_fields as string[]).map((field) => field.toLowerCase()));
  const deniedFields = new Set((value.denied_fields as string[]).map((field) => field.toLowerCase()));
  if ([...allowedFields].some((field) => RAW_FIELD_PATTERN.test(field))) return false;
  if (ALL_DENIED_SUMMARY_CATEGORIES.some((field) => allowedFields.has(field))) return false;
  const hasCredentialBoundary =
    deniedFields.has(ABSTRACT_CREDENTIAL_MATERIAL_CATEGORY) ||
    LEGACY_CREDENTIAL_DENIED_SAFETY_CATEGORIES.every((field) => deniedFields.has(field));
  const hasLocalOnlyBoundary =
    deniedFields.has(ABSTRACT_LOCAL_ONLY_IDENTIFIER_CATEGORY) || deniedFields.has(INTERNAL_FIELD_NAMES.localEnvironmentPath);
  return (
    BASE_REQUIRED_DENIED_SAFETY_CATEGORIES.every((field) => deniedFields.has(field)) &&
    hasCredentialBoundary &&
    hasLocalOnlyBoundary
  );
}

function validateFailClosed(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, FAIL_CLOSED_KEYS)) return false;
  if (value.fallback_required !== true) return false;
  if (!hasString(value, "fallback_target") || !hasStringArray(value, "reject_when")) return false;
  const rejectReasons = new Set((value.reject_when as string[]).map((field) => field.toLowerCase()));
  return (
    REQUIRED_REJECT_REASONS.every((reason) => rejectReasons.has(reason)) &&
    RAW_OR_CREDENTIAL_REJECT_REASONS.some((reason) => rejectReasons.has(reason))
  );
}

function validateRulePack(pack: unknown): pack is RulePack {
  if (!isRecord(pack)) return false;
  return (
    hasExactKeys(pack, RULE_PACK_KEYS) &&
    hasString(pack, "id") &&
    hasString(pack, "name") &&
    hasString(pack, "intent") &&
    hasStringArray(pack, "influenceAxes") &&
    hasStringArray(pack, "directives") &&
    hasStringArray(pack, "negativeConstraints")
  );
}

function validateRulePacks(value: unknown): value is RulePack[] {
  return Array.isArray(value) && value.length > 0 && value.every(validateRulePack);
}

function validateSceneMapping(value: unknown): value is KbSnapshot["sceneMappings"][string] {
  if (!isRecord(value) || !hasExactKeys(value, SCENE_MAPPING_KEYS)) return false;
  return (
    hasStringArray(value, "writingRulePackIds") &&
    hasStringArray(value, "directorRulePackIds") &&
    hasStringArray(value, "validationRulePackIds") &&
    hasString(value, "sceneProfile") &&
    hasStringArray(value, "negativeConstraints") &&
    hasStringArray(value, "influenceAxes")
  );
}

function validateDurationProfile(value: unknown): value is KbSnapshot["durationProfiles"][number] {
  if (!isRecord(value) || !hasExactKeys(value, DURATION_PROFILE_KEYS)) return false;
  return (
    Number.isInteger(value.duration) &&
    Number(value.duration) > 0 &&
    Number.isInteger(value.targetShotCount) &&
    Number(value.targetShotCount) > 0 &&
    hasString(value, "beatDensity") &&
    hasString(value, "pacingDirective")
  );
}

function collectRulePackIds(snapshot: KbSnapshot): Set<string> {
  return new Set(
    [...snapshot.writingRulePacks, ...snapshot.directorRulePacks, ...snapshot.validationRulePacks].map((pack) => pack.id),
  );
}

function validateSnapshotShape(value: unknown): value is KbSnapshot {
  if (!isRecord(value)) return false;
  if (!hasExactKeys(value, SNAPSHOT_KEYS)) return false;
  if (!hasString(value, "snapshotVersion")) return false;
  if (!hasStringArray(value, "sceneTypes") || !hasUniqueItems(value.sceneTypes as string[])) return false;
  if (!hasNumberArray(value, "allowedDurations") || !hasUniqueItems(value.allowedDurations as number[])) return false;
  if (!validateRulePacks(value.writingRulePacks)) return false;
  if (!validateRulePacks(value.directorRulePacks)) return false;
  if (!validateRulePacks(value.validationRulePacks)) return false;
  if (
    !Array.isArray(value.durationProfiles) ||
    value.durationProfiles.length === 0 ||
    !value.durationProfiles.every(validateDurationProfile)
  ) {
    return false;
  }
  if (!isRecord(value.sceneMappings)) return false;
  if (!Object.values(value.sceneMappings).every(validateSceneMapping)) return false;
  if (!(value.sceneTypes as string[]).every((sceneType) => validateSceneMapping((value.sceneMappings as Record<string, unknown>)[sceneType]))) {
    return false;
  }
  if (!Object.keys(value.sceneMappings).every((sceneType) => (value.sceneTypes as string[]).includes(sceneType))) {
    return false;
  }
  return true;
}

function validateSnapshotReferences(snapshot: KbSnapshot): string | undefined {
  const rulePackIds = collectRulePackIds(snapshot);
  for (const sceneType of snapshot.sceneTypes) {
    const mapping = snapshot.sceneMappings[sceneType];
    if (!validateSceneMapping(mapping)) return `missing scene mapping: ${sceneType}`;
    const referenced = [
      ...mapping.writingRulePackIds,
      ...mapping.directorRulePackIds,
      ...mapping.validationRulePackIds,
    ];
    const missing = referenced.find((rulePackId) => !rulePackIds.has(rulePackId));
    if (missing) return `missing rule pack reference: ${sceneType} -> ${missing}`;
  }
  for (const duration of snapshot.allowedDurations) {
    if (!snapshot.durationProfiles.some((profile) => profile.duration === duration)) {
      return `missing duration profile: ${duration}`;
    }
  }
  return undefined;
}

export function compilePwaKbAdapterOutput(
  candidate: unknown,
  options: CompileAdapterOptions = {},
): CompileAdapterResult {
  if (!isRecord(candidate)) return { accepted: false, rejectReason: "adapter output is not an object" };
  if (containsDeniedRawSignal(candidate)) {
    return { accepted: false, rejectReason: "adapter output contains denied raw/internal field" };
  }
  if (!hasExactKeys(candidate, ADAPTER_OUTPUT_KEYS)) {
    return { accepted: false, rejectReason: "adapter output contains unsupported or missing fields" };
  }
  if (candidate.adapter_version !== ADAPTER_VERSION) return { accepted: false, rejectReason: "unsupported adapter version" };
  if (!isOneOf(candidate.adapter_status, ADAPTER_STATUSES)) {
    return { accepted: false, rejectReason: "unsupported adapter status" };
  }
  if (!isOneOf(candidate.scene_catalog_status, SCENE_CATALOG_STATUSES)) {
    return { accepted: false, rejectReason: "unsupported scene catalog status" };
  }
  if (!isOneOf(candidate.rule_pack_crosswalk_status, RULE_PACK_CROSSWALK_STATUSES)) {
    return { accepted: false, rejectReason: "unsupported rule pack crosswalk status" };
  }
  if (candidate.adapter_status === "prototype" && !options.allowPrototype) {
    return { accepted: false, rejectReason: "prototype adapter output requires explicit opt-in" };
  }
  if (candidate.rule_pack_crosswalk_status === "prototype" && candidate.adapter_status !== "prototype") {
    return { accepted: false, rejectReason: "prototype rule pack crosswalk requires prototype adapter status" };
  }
  if (candidate.rule_pack_crosswalk_status === "prototype" && !options.allowPrototype) {
    return { accepted: false, rejectReason: "prototype rule pack crosswalk requires explicit opt-in" };
  }
  if (candidate.scene_catalog_status === "partial" && !options.allowPartialSceneCatalog) {
    return { accepted: false, rejectReason: "partial scene catalog requires explicit opt-in" };
  }
  if (!hasString(candidate, "source_snapshot_version")) {
    return { accepted: false, rejectReason: "source snapshot version is required" };
  }
  if (typeof candidate.source_snapshot_hash !== "string" || !HASH_PATTERN.test(candidate.source_snapshot_hash)) {
    return { accepted: false, rejectReason: "invalid source snapshot hash" };
  }
  if (candidate.adapter_status !== "prototype" && candidate.source_snapshot_hash.includes("sample-")) {
    return { accepted: false, rejectReason: "sample source snapshot hash is limited to prototype adapter output" };
  }
  if (!validateFailClosed(candidate.fail_closed)) {
    return { accepted: false, rejectReason: "fail-closed fallback is required" };
  }
  if (!validateSummaryContract(candidate.sanitized_summary_contract)) {
    return { accepted: false, rejectReason: "summary-only contract is required" };
  }
  if (!validateSnapshotShape(candidate.pwa_snapshot)) {
    return { accepted: false, rejectReason: "adapter snapshot does not match PWA KbSnapshot shape" };
  }
  const referenceError = validateSnapshotReferences(candidate.pwa_snapshot);
  if (referenceError) return { accepted: false, rejectReason: referenceError };
  return { accepted: true, snapshot: candidate.pwa_snapshot };
}

export async function loadPwaKbSnapshot(options: LoadAdapterOptions = {}): Promise<LoadAdapterResult> {
  const fallbackSnapshot = options.fallbackSnapshot ?? KB_SNAPSHOT;
  const fetcher = options.fetcher ?? fetch;
  const url = options.url ?? "/kb/latest.json";

  try {
    const response = await fetcher(url, { cache: "no-store" });
    if (!response.ok) {
      return { snapshot: fallbackSnapshot, source: "fallback", rejectReason: `adapter fetch failed: ${response.status}` };
    }
    const payload = await response.json();
    const compiled = compilePwaKbAdapterOutput(payload, options);
    if (!compiled.accepted || !compiled.snapshot) {
      return { snapshot: fallbackSnapshot, source: "fallback", rejectReason: compiled.rejectReason };
    }
    return { snapshot: compiled.snapshot, source: "external" };
  } catch {
    return { snapshot: fallbackSnapshot, source: "fallback", rejectReason: "adapter load failed" };
  }
}
