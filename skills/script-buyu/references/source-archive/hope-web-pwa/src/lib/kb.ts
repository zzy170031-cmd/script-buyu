import { sha256Hex, stableStringify } from "./hash";
import { getSceneTypeLabel, getSceneTypeOption, SCENE_TYPE_CANONICAL_LIST } from "./sceneTypes";
import { SUMMARY_GUARD_FIELDS } from "./safetyFields";
import type {
  DurationCapacityProfile,
  KbAction,
  KbActionResult,
  KbRuleGroup,
  KbSnapshot,
  RulePack,
  SanitizedKbSummary,
} from "./types";

export const STRUCTURE_ACTIONS: KbAction[] = ["create_story_task", "generate_storyboard", "repair_storyboard"];

const writingRulePacks: RulePack[] = [
  {
    id: "wg-complete-body",
    name: "正文完整性",
    intent: "确保正文是用户可确认的连续叙事，而不是镜头清单或规则说明。",
    influenceAxes: ["source_facts", "event_order", "character_continuity"],
    directives: [
      "保留源文本中的人物、地点、冲突和事件顺序。",
      "输出连续正文，而不是分镜表或提示词。",
      "让 accepted body 足够完整，方便后续创建镜头任务。",
    ],
    negativeConstraints: ["不得输出原始知识行", "不得输出原始样例", "不得输出内部来源登记或提示词中间件"],
  },
  {
    id: "wg-scene-expression",
    name: "场景表达适配",
    intent: "让正文在不改事实的前提下体现当前 scene_type 的情绪与空间气质。",
    influenceAxes: ["scene_expression", "duration_density"],
    directives: [
      "scene_type 只影响表达方式，不改人物与事件事实。",
      "把当前场景的空间压迫、情绪推进和动作节奏写进正文。",
      "让 target duration 反映为叙事密度，而不是字数堆砌。",
    ],
    negativeConstraints: ["不得把 scene_type 当成人物或地点", "不得凭空添加新世界观事实"],
  },
  {
    id: "wg-beat-discipline",
    name: "节拍纪律",
    intent: "保持动作、对白、叙述之间可拆镜的节拍感。",
    influenceAxes: ["duration_density", "event_order"],
    directives: [
      "每段推进一个明确动作或情绪节拍。",
      "对白只在必要时出现，避免整段对话堆积。",
      "保证导演组能够从正文拆出连续可见镜头。",
    ],
    negativeConstraints: ["不得用抽象抒情代替动作", "不得把对白写成说明书"],
  },
];

const directorRulePacks: RulePack[] = [
  {
    id: "dg-visible-frame",
    name: "当前镜头可见帧",
    intent: "每条分镜只描述当前镜头里真实能看见的内容。",
    influenceAxes: ["visual_grounding", "structure"],
    directives: [
      "visual_description 只写当前镜头可见的人、动作、空间和冲突。",
      "person 只能来自 accepted body 中真实存在的人物或角色标签。",
      "不要把规则名、trace 或内部字段写进画面描述。",
    ],
    negativeConstraints: ["不得用抽象词代替画面", "不得把 UI、镜头、构图等写进 person"],
  },
  {
    id: "dg-prompt-compile",
    name: "提示词编译",
    intent: "把 accepted body、场景意图和导演约束整理成可执行 prompt_text。",
    influenceAxes: ["prompt_boundary", "visual_grounding"],
    directives: [
      "prompt_text 必须覆盖主体、动作、画面、镜头、时长和负面约束。",
      "prompt_text 必须与 visual_description 对齐，不能脱离 accepted body。",
      "输出面向生成的自然语言提示，而不是内部规则 ID。",
    ],
    negativeConstraints: ["不得输出空 prompt_text", "不得泄漏 raw sample_text 或内部证据"],
  },
  {
    id: "dg-duration-pacing",
    name: "时长节奏分配",
    intent: "按 5/10/15/30/45/60 秒容量分配镜头数与节奏。",
    influenceAxes: ["duration_density", "structure"],
    directives: [
      "所有镜头时长总和必须严格等于 target_duration_seconds。",
      "每条镜头都要承载可见动作、情绪推进或空间信息。",
      "允许 15 秒内出现 10 + 5 之类的结构分配，但不允许空镜头占位。",
    ],
    negativeConstraints: ["rows=0 不能当成功", "不得输出零时长镜头"],
  },
];

const validationRulePacks: RulePack[] = [
  {
    id: "vg-no-pseudo-success",
    name: "伪成功阻断",
    intent: "禁止 rows=0、prompt 缺失或 blocked 结果伪装为成功。",
    influenceAxes: ["validation_gate", "export_safety"],
    directives: [
      "rows 非空、prompt_text 非空、visual_description 非空才允许通过。",
      "blocked export 只能是 blocked，不能标成 success。",
      "repair_storyboard 必须是独立动作，不能在校验阶段偷偷修复。",
    ],
    negativeConstraints: ["不得把校验当修复", "不得把 rows_match=true 且 rows=0 当成功"],
  },
  {
    id: "vg-no-leakage",
    name: "泄漏阻断",
    intent: "阻断原始知识、样例、来源登记、覆盖层、中间提示词和内部引用泄漏。",
    influenceAxes: ["prompt_boundary", "export_safety", "source_lineage"],
    directives: [
      "prompt、UI、导出都必须是 summary-only。",
      "禁止向用户暴露 sample ids、rule ids、hash refs 和内部 provenance。",
      "保留用户可读 blocked reason，但不暴露内部调试面。",
    ],
    negativeConstraints: ["不得泄漏 raw sample_text", "不得泄漏 accepted_body_hash、rows_hash 等内部 refs"],
  },
  {
    id: "vg-field-aware-entity",
    name: "字段感知实体校验",
    intent: "阻断 person 字段被地点、动作碎片、场景词或占位词污染。",
    influenceAxes: ["validation_gate", "visual_grounding"],
    directives: [
      "person 必须是人物名或可信角色标签。",
      "location/action/scene 片段不得流入 person。",
      "主角/路人/某人 等泛化占位词不得直接通过。",
    ],
    negativeConstraints: ["不得把环境词当人物", "不得把动作碎片当人物"],
  },
];

const durationProfiles: DurationCapacityProfile[] = [
  { duration: 5, targetShotCount: 3, beatDensity: "high", pacingDirective: "三镜内完成冲突起落与钩子落点。" },
  { duration: 10, targetShotCount: 4, beatDensity: "high", pacingDirective: "四镜内明确空间、人物关系和主冲突推进。" },
  { duration: 15, targetShotCount: 5, beatDensity: "medium", pacingDirective: "五镜形成完整小节拍，允许 10 + 5 的分配。" },
  { duration: 30, targetShotCount: 7, beatDensity: "medium", pacingDirective: "七镜保留一组呼吸镜头，但主冲突持续可见。" },
  { duration: 45, targetShotCount: 9, beatDensity: "layered", pacingDirective: "九镜兼顾主线与副动作，允许空间调度与视线转换。" },
  { duration: 60, targetShotCount: 12, beatDensity: "layered", pacingDirective: "十二镜完成完整段落，多层推进但不能失焦。" },
];

const ACTION_PRIMARY_GROUP: Record<KbAction, KbRuleGroup> = {
  import_source: "validation_group",
  expand_story: "writing_group",
  rewrite_story: "writing_group",
  accept_story_body: "validation_group",
  create_story_task: "director_group",
  generate_storyboard: "director_group",
  repair_storyboard: "director_group",
  validate_result: "validation_group",
  export_result: "validation_group",
  golden_sample_review: "validation_group",
};

const ACTION_SECONDARY_GROUPS: Record<KbAction, KbRuleGroup[]> = {
  import_source: ["writing_group"],
  expand_story: ["validation_group"],
  rewrite_story: ["validation_group"],
  accept_story_body: ["writing_group"],
  create_story_task: ["writing_group"],
  generate_storyboard: ["validation_group"],
  repair_storyboard: ["validation_group", "writing_group"],
  validate_result: [],
  export_result: [],
  golden_sample_review: ["writing_group", "director_group"],
};

const ACTION_INFLUENCE_AXES: Record<KbAction, string[]> = {
  import_source: ["source_lineage", "validation_gate"],
  expand_story: ["source_facts", "character_continuity", "event_order", "scene_expression", "duration_density"],
  rewrite_story: ["source_facts", "character_continuity", "event_order", "scene_expression"],
  accept_story_body: ["source_lineage", "validation_gate"],
  create_story_task: ["scene_expression", "duration_density", "structure"],
  generate_storyboard: ["structure", "visual_grounding", "prompt_boundary", "duration_density"],
  repair_storyboard: ["validation_gate", "structure", "visual_grounding", "prompt_boundary"],
  validate_result: ["validation_gate", "visual_grounding", "prompt_boundary", "source_lineage"],
  export_result: ["export_safety", "validation_gate", "source_lineage"],
  golden_sample_review: ["validation_gate", "source_facts", "prompt_boundary"],
};

function resolveWritingRulePackIds(sceneType: string): string[] {
  const family = getSceneTypeOption(sceneType).family;
  if (family === "conflict") {
    return ["wg-complete-body", "wg-scene-expression"];
  }
  if (family === "epic") {
    return ["wg-complete-body", "wg-scene-expression", "wg-beat-discipline"];
  }
  return ["wg-complete-body", "wg-beat-discipline", "wg-scene-expression"];
}

function resolveDirectorRulePackIds(sceneType: string): string[] {
  const family = getSceneTypeOption(sceneType).family;
  if (family === "performance") {
    return ["dg-visible-frame", "dg-prompt-compile"];
  }
  return ["dg-visible-frame", "dg-prompt-compile", "dg-duration-pacing"];
}

function resolveValidationRulePackIds(): string[] {
  return ["vg-no-pseudo-success", "vg-no-leakage", "vg-field-aware-entity"];
}

function resolveInfluenceAxes(
  writingRulePackIds: string[],
  directorRulePackIds: string[],
  validationRulePackIds: string[],
): string[] {
  return Array.from(
    new Set(
      [...writingRulePackIds, ...directorRulePackIds, ...validationRulePackIds].flatMap((id) => {
        const pack = [...writingRulePacks, ...directorRulePacks, ...validationRulePacks].find((item) => item.id === id);
        return pack?.influenceAxes ?? [];
      }),
    ),
  );
}

function resolveSceneProfile(sceneType: string): string {
  const option = getSceneTypeOption(sceneType);
  switch (option.family) {
    case "conflict":
      return `${option.label}要求画面持续可见冲突压力、位移关系和动作落点，不能只剩抽象紧张感。`;
    case "performance":
      return `${option.label}要求人物关系、情绪推力和表演细节同时可见，镜头要服务角色互动。`;
    case "spectacle":
      return `${option.label}要求奇观、空间层次和视觉焦点清晰落地，不能退化成泛环境描写。`;
    case "epic":
      return `${option.label}要求秩序关系、阵线变化和宏观推进具备可视化组织。`;
    default:
      return `${option.label}要求正文和分镜都建立清晰的空间、情绪和动作推进。`;
  }
}

function resolveNegativeConstraints(sceneType: string): string[] {
  const option = getSceneTypeOption(sceneType);
  const shared = [
    "禁止泄漏 API Key、原始知识行、原始样例文本、内部来源登记、覆盖层元数据或提示词中间件。",
    "禁止把人物、地点、KB、UI、构图词当作 scene_type 或 person。",
    "禁止把旧 rows、旧 task、旧 accepted body 当作当前事实源。",
    "禁止向用户暴露 sample ids、rule ids、hash refs 或内部 provenance。",
  ];
  if (option.family === "epic") {
    return [...shared, "禁止空泛宏大叙述掩盖当前镜头应见的具体动作。"];
  }
  if (option.family === "performance") {
    return [...shared, "禁止只写情绪标签而不写可见表演动作。"];
  }
  return [...shared, "禁止用抽象词替代当前镜头可见画面。"];
}

function resolveSelectedSampleIds(sceneType: string): string[] {
  return [`sample-${sceneType}-A`, `sample-${sceneType}-B`, `sample-${sceneType}-C`];
}

function resolveSelectedKbRules(sceneType: string, duration: number): string[] {
  const option = getSceneTypeOption(sceneType);
  return [
    `scene-profile:${sceneType}`,
    `family:${option.family}`,
    `duration:${duration}`,
    "validation:no-pseudo-success",
    "validation:no-leakage",
    "validation:field-aware-entity",
  ];
}

function actionSummary(action: KbAction): string {
  switch (action) {
    case "import_source":
      return "导入动作只输出 summary-only 的源事实准备度，不暴露 raw source。";
    case "expand_story":
      return "写作组负责扩写正文，保留事实、关系和事件顺序。";
    case "rewrite_story":
      return "写作组负责改写正文，保留事实并整理表达。";
    case "accept_story_body":
      return "验证组负责 accepted body 锁定前的完整性与血缘校验。";
    case "create_story_task":
      return "写作组把 accepted body 转成 scene / storyboard task 的规划输入。";
    case "generate_storyboard":
      return "导演组负责镜头结构、visual grounding 和 prompt 编译。";
    case "repair_storyboard":
      return "repair_storyboard 是独立动作，只在失败后针对性修复。";
    case "validate_result":
      return "验证组负责 non-empty rows、field-aware entity、prompt boundary 和 no-pseudo-success。";
    case "export_result":
      return "验证组负责 export safety 和零泄漏后才允许导出。";
    case "golden_sample_review":
      return "golden sample review 只用于预期校验，不把 raw sample 变成 runtime payload。";
    default:
      return "";
  }
}

function buildActionResult(action: KbAction): KbActionResult {
  return {
    action,
    primary_group: ACTION_PRIMARY_GROUP[action],
    secondary_groups: [...ACTION_SECONDARY_GROUPS[action]],
    state: "ready",
    summary: actionSummary(action),
    blocked_reason: "",
    influence_axes: [...ACTION_INFLUENCE_AXES[action]],
    kb_oracle_affects_structure: STRUCTURE_ACTIONS.includes(action),
  };
}

function buildKbContextSummary(sceneType: string, sceneProfile: string, durationProfile: DurationCapacityProfile): string {
  const option = getSceneTypeOption(sceneType);
  return [
    `${option.label}场景下，写作组负责 accepted body 的事实连续性与场景表达。`,
    `导演组负责镜头结构、可见画面与 prompt 编译，目标时长 ${durationProfile.duration} 秒，建议 ${durationProfile.targetShotCount} 镜。`,
    `验证组负责 no-pseudo-success、field-aware entity 与 export safety。`,
    `当前场景摘要：${sceneProfile}`,
  ].join(" ");
}

const sceneMappings = Object.fromEntries(
  SCENE_TYPE_CANONICAL_LIST.map((sceneType) => {
    const writingRulePackIds = resolveWritingRulePackIds(sceneType);
    const directorRulePackIds = resolveDirectorRulePackIds(sceneType);
    const validationRulePackIds = resolveValidationRulePackIds();
    const sceneProfile = resolveSceneProfile(sceneType);
    return [
      sceneType,
      {
        writingRulePackIds,
        directorRulePackIds,
        validationRulePackIds,
        sceneProfile,
        negativeConstraints: resolveNegativeConstraints(sceneType),
        influenceAxes: resolveInfluenceAxes(writingRulePackIds, directorRulePackIds, validationRulePackIds),
      },
    ];
  }),
) as KbSnapshot["sceneMappings"];

export const KB_SNAPSHOT: KbSnapshot = {
  snapshotVersion: "hope-web-kb-snapshot-v4",
  sceneTypes: [...SCENE_TYPE_CANONICAL_LIST],
  allowedDurations: durationProfiles.map((item) => item.duration),
  writingRulePacks,
  directorRulePacks,
  validationRulePacks,
  sceneMappings,
  durationProfiles,
};

let kbSnapshotHashPromise: Promise<string> | null = null;

export function getRulePackById(rulePackId: string): RulePack | undefined {
  return [...writingRulePacks, ...directorRulePacks, ...validationRulePacks].find((item) => item.id === rulePackId);
}

export function getRulePackByIdFromSnapshot(snapshot: KbSnapshot, rulePackId: string): RulePack | undefined {
  return [...snapshot.writingRulePacks, ...snapshot.directorRulePacks, ...snapshot.validationRulePacks].find(
    (item) => item.id === rulePackId,
  );
}

export function getDurationProfile(duration: number): DurationCapacityProfile {
  return durationProfiles.find((item) => item.duration === duration) ?? durationProfiles[2];
}

export function getDurationProfileFromSnapshot(snapshot: KbSnapshot, duration: number): DurationCapacityProfile {
  return snapshot.durationProfiles.find((item) => item.duration === duration) ?? getDurationProfile(duration);
}

export function isAllowedDuration(duration: number): boolean {
  return KB_SNAPSHOT.allowedDurations.includes(duration);
}

export function isKbAction(value: string): value is KbAction {
  return (
    value === "import_source" ||
    value === "expand_story" ||
    value === "rewrite_story" ||
    value === "accept_story_body" ||
    value === "create_story_task" ||
    value === "generate_storyboard" ||
    value === "repair_storyboard" ||
    value === "validate_result" ||
    value === "export_result" ||
    value === "golden_sample_review"
  );
}

export function primaryGroupForAction(action: KbAction): KbRuleGroup {
  return ACTION_PRIMARY_GROUP[action];
}

export function secondaryGroupsForAction(action: KbAction): KbRuleGroup[] {
  return [...ACTION_SECONDARY_GROUPS[action]];
}

export function defaultActionResults(): KbActionResult[] {
  return [
    buildActionResult("import_source"),
    buildActionResult("expand_story"),
    buildActionResult("rewrite_story"),
    buildActionResult("accept_story_body"),
    buildActionResult("create_story_task"),
    buildActionResult("generate_storyboard"),
    buildActionResult("repair_storyboard"),
    buildActionResult("validate_result"),
    buildActionResult("export_result"),
    buildActionResult("golden_sample_review"),
  ];
}

export function withActionResult(
  actionResults: KbActionResult[],
  action: KbAction,
  patch: Partial<KbActionResult>,
): KbActionResult[] {
  return actionResults.map((item) => (item.action === action ? { ...item, ...patch } : item));
}

export async function getKbSnapshotHash(): Promise<string> {
  if (!kbSnapshotHashPromise) {
    kbSnapshotHashPromise = sha256Hex(stableStringify(KB_SNAPSHOT));
  }
  return kbSnapshotHashPromise;
}

export async function getKbSnapshotHashFromSnapshot(snapshot: KbSnapshot): Promise<string> {
  if (snapshot === KB_SNAPSHOT) {
    return getKbSnapshotHash();
  }
  return sha256Hex(stableStringify(snapshot));
}

export async function buildSanitizedKbSummary(sceneType: string, duration: number): Promise<SanitizedKbSummary> {
  return buildSanitizedKbSummaryFromSnapshot(KB_SNAPSHOT, sceneType, duration);
}

export async function buildSanitizedKbSummaryFromSnapshot(
  snapshot: KbSnapshot,
  sceneType: string,
  duration: number,
): Promise<SanitizedKbSummary> {
  const sceneTypeId = snapshot.sceneTypes.includes(sceneType) ? sceneType : (snapshot.sceneTypes[0] ?? SCENE_TYPE_CANONICAL_LIST[0]);
  const mapping = snapshot.sceneMappings[sceneTypeId] ?? sceneMappings[sceneTypeId] ?? sceneMappings[SCENE_TYPE_CANONICAL_LIST[0]];
  const sceneProfile = mapping.sceneProfile;
  const allowedDurations = snapshot.allowedDurations.length > 0 ? snapshot.allowedDurations : KB_SNAPSHOT.allowedDurations;
  const effectiveDuration = allowedDurations.includes(duration) ? duration : (allowedDurations[0] ?? duration);
  const durationProfile = getDurationProfileFromSnapshot(snapshot, effectiveDuration);
  const actionResults = defaultActionResults();

  return {
    kb_snapshot_hash: await getKbSnapshotHashFromSnapshot(snapshot),
    scene_type_count: snapshot.sceneTypes.length,
    scene_type_id: sceneTypeId,
    scene_type_label: getSceneTypeLabel(sceneTypeId),
    duration_options: [...allowedDurations],
    selected_sample_ids: resolveSelectedSampleIds(sceneTypeId),
    selected_kb_rules: resolveSelectedKbRules(sceneTypeId, effectiveDuration),
    writing_group_rule_pack_ids: [...mapping.writingRulePackIds],
    director_group_rule_pack_ids: [...mapping.directorRulePackIds],
    validation_group_rule_pack_ids: [...mapping.validationRulePackIds],
    kb_context_summary: buildKbContextSummary(sceneTypeId, sceneProfile, durationProfile),
    applied_to: [
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
    ],
    action_results: actionResults,
    influence_axes: [...mapping.influenceAxes],
    scene_profile: sceneProfile,
    negative_constraints: [...mapping.negativeConstraints],
    kb_oracle_affects_structure: true,
    [SUMMARY_GUARD_FIELDS.rawKbRowsIncluded]: 0,
    raw_sample_text_absent: true,
    [SUMMARY_GUARD_FIELDS.sourceRegisterAbsent]: true,
    overlay_json_absent: true,
    [SUMMARY_GUARD_FIELDS.promptBodyAbsent]: true,
  };
}
