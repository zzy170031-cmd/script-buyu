import { getDurationProfileFromSnapshot, getRulePackByIdFromSnapshot } from "./kb";
import { summarizeFacts } from "./facts";
import { buildSensitiveTermPattern, INTERNAL_FIELD_PARTS } from "./safetyFields";
import type { GenerationContext, KbSnapshot, SourceFacts, StoryboardRow, StoryboardTask } from "./types";

interface ChatMessage {
  role: "system" | "user";
  content: string;
}

const PROMPT_PAYLOAD_INTERNAL_PATTERN = buildSensitiveTermPattern(
  [
    INTERNAL_FIELD_PARTS.rawKb,
    ["raw", "source"],
    INTERNAL_FIELD_PARTS.sourceRefs,
    INTERNAL_FIELD_PARTS.sourceUrl,
    INTERNAL_FIELD_PARTS.sourceTitle,
    INTERNAL_FIELD_PARTS.sourceRegister,
    INTERNAL_FIELD_PARTS.overlayJson,
    INTERNAL_FIELD_PARTS.promptBody,
  ],
  [
    "ocr",
    "sample ids?",
    "rule ids?",
    "schema ids?",
    "internal hashes?",
    "hash refs?",
    "local paths?",
    String.raw`api\s*key`,
    "secret",
    "token",
    "validator trace",
    String.raw`[a-z]:\\`,
    String.raw`\\\\`,
  ],
);
const PROMPT_PAYLOAD_INTERNAL_GUARD = "不得输出内部来源资料、治理元数据、调试痕迹或凭证信息。";

function safePromptPayloadLine(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "";
  }
  return PROMPT_PAYLOAD_INTERNAL_PATTERN.test(normalized) ? PROMPT_PAYLOAD_INTERNAL_GUARD : normalized;
}

function safePromptPayloadLines(values: string[]): string[] {
  return Array.from(new Set(values.map(safePromptPayloadLine).filter(Boolean)));
}

function ruleLines(ids: string[], kbSnapshot: KbSnapshot): string[] {
  return ids.flatMap((id) => {
    const pack = getRulePackByIdFromSnapshot(kbSnapshot, id);
    if (!pack) {
      return [];
    }
    return [
      `- ${pack.name}`,
      ...safePromptPayloadLines(pack.directives).map((item) => `  - ${item}`),
      ...safePromptPayloadLines(pack.negativeConstraints).map((item) => `  - 禁止：${item}`),
    ];
  });
}

function modeLabel(mode: GenerationContext["mode"]): string {
  return mode === "rewrite_story" ? "改写剧本" : "扩写故事";
}

const INTERNAL_PROMPT_TERMS_PATTERN = buildSensitiveTermPattern(
  [
    INTERNAL_FIELD_PARTS.rawKb,
    INTERNAL_FIELD_PARTS.rawSample,
    INTERNAL_FIELD_PARTS.sampleText,
    INTERNAL_FIELD_PARTS.sourceRegister,
    INTERNAL_FIELD_PARTS.overlayJson,
    INTERNAL_FIELD_PARTS.promptBody,
  ],
  [
    "sample ids?",
    "rule ids?",
    "rule pack",
    "hash refs?",
    "provenance",
    "写作组",
    "导演组",
    "验证组",
    "制作参考",
    "validator",
    "validator taxonomy",
    "no-pseudo-success",
    "field-aware entity",
    "export safety",
    "writing_group",
    "director_group",
    "validation_group",
    "kb_context_summary",
    "selected_kb_rules",
    "selected_sample_ids",
  ],
);
const CAMERA_PROMPT_TERMS = ["固定机位", "定镜", "推进", "跟拍", "摇镜", "拉远", "环绕", "俯拍", "低机位", "横移", "平移", "航拍", "推近", "后拉"];
const CAMERA_PRODUCTION_DETAIL_PATTERN = /(\b\d{1,3}\s*mm\b|毫米|焦段|焦距|广角|长焦|标准焦段|三脚架|手持|肩扛|器材|镜头随|光圈|景深|制作术语)/i;

function userFacingVisualConstraint(sceneLabel: string): string {
  return `${sceneLabel}风格下保持人物身份、关键道具、空间关系和当前镜头可见内容一致。`;
}

function cleanPromptLine(value: string, fallback: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return fallback;
  }
  return INTERNAL_PROMPT_TERMS_PATTERN.test(normalized) ? fallback : normalized;
}

function cleanCameraPromptLine(value: string, fallback: string): string {
  const normalized = cleanPromptLine(value, fallback);
  if (normalized === fallback) {
    return normalized;
  }
  const primaryMovement = CAMERA_PROMPT_TERMS.find((term) => normalized.includes(term));
  if (CAMERA_PRODUCTION_DETAIL_PATTERN.test(normalized) || /[，,；;、]/.test(normalized) || normalized.length > 24) {
    return primaryMovement ?? fallback;
  }
  return normalized;
}

function userFacingPacing(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  const totalMatch = normalized.match(/总时长\s*(\d+)\s*s/i);
  const totalPrefix = totalMatch ? `总时长 ${totalMatch[1]} 秒，` : "";
  return `${totalPrefix}镜头节奏围绕当前场景的动作、空间和情绪变化展开，不按固定秒数机械切分。`;
}

function bodyDurationCapacity(targetDurationSeconds: number): string {
  const minChars = Math.max(220, Math.round(targetDurationSeconds * 16));
  const maxChars = Math.max(minChars + 160, Math.round(targetDurationSeconds * 26));
  const beatCount = Math.max(2, Math.ceil(targetDurationSeconds / 8));
  return `正文容量需匹配 ${targetDurationSeconds} 秒目标：建议 ${beatCount} 个以上清晰动作/情绪/空间拍点，约 ${minChars}-${maxChars} 个中文字符；不得用短片段代替长时长正文。`;
}

export function buildConnectionTestMessages(model: string): ChatMessage[] {
  return [
    {
      role: "system",
      content: "You are a connection probe. Respond with one short sentence confirming the model is reachable.",
    },
    {
      role: "user",
      content: `Model handshake check for ${model}. Reply with: reachable`,
    },
  ];
}

export function buildWritingMessages(context: GenerationContext, facts: SourceFacts): ChatMessage[] {
  const durationProfile = getDurationProfileFromSnapshot(context.kbSnapshot, context.targetDuration);
  return [
    {
      role: "system",
      content: [
        "你是 Hope Web 的写作组，不是提示词生成器。",
        "你的任务是把用户输入和 KB 写作组摘要组织成可确认的完整正文。",
        "KB 写作组摘要、场景 profile 与 writing_group_rules 是正文风格、节奏和镜头感的执行依据，不是可忽略背景。",
        "正文要吸收黄金样本式的场景压迫、动作因果、空间调度、情绪推进和可视化细节，不能只复述梗概或扩写成空泛摘要。",
        "正文必须是用户可直接确认的故事文本，不得输出分镜表、提示词草稿、内部知识原文、调试结构或控制字段。",
      ].join("\n"),
    },
    {
      role: "user",
      content: [
        `动作: ${modeLabel(context.mode)}`,
        `scene_type_id: ${context.sceneTypeId}`,
        `scene_type_label: ${context.sceneTypeLabel}`,
        `target_duration_seconds: ${context.targetDuration}`,
        `writing_summary: ${context.kbSummary.kb_context_summary}`,
        `scene_profile: ${context.kbSummary.scene_profile}`,
        `duration_capacity: ${durationProfile.pacingDirective}`,
        `body_duration_capacity: ${bodyDurationCapacity(context.targetDuration)}`,
        "writing_group_rules:",
        ...ruleLines(context.kbSummary.writing_group_rule_pack_ids, context.kbSnapshot),
        "negative_constraints:",
        ...safePromptPayloadLines(context.kbSummary.negative_constraints).map((item) => `- ${item}`),
        "local_source_facts:",
        summarizeFacts(facts),
        "user_source_text:",
        context.sourceText,
        "输出要求：",
        "- 输出 JSON 对象。",
        "- title: 故事标题。",
        "- body: 至少两段的完整正文。",
        "- body 的内容密度必须匹配 target_duration_seconds；60 秒目标必须给出足够的连续情节与画面推进，不能只输出 15 秒容量的短文本。",
        "- 必须把 writing_summary、scene_profile、writing_group_rules 和 local_source_facts 作为写作依据来组织正文；不能只改写 user_source_text。",
        "- 每段都要包含可见空间、人物动作、冲突压力、情绪或节奏变化，保持黄金样本式的镜头感和叙事密度。",
        "- expand_story 要在事实守恒下补足动作因果、视觉细节和节奏转折；rewrite_story 也必须提升画面表达，不得压缩事实。",
        "- body 不得是摘要、纲要、短梗概或只换词，长时长必须扩展为可继续拆分分镜的连续正文。",
        "- 保留真实人物、地点、冲突和事件顺序；scene_type 只改变表达方式，不改变事实。",
        "- 对白/旁白只能保留 user_source_text 中明确存在的对白或旁白；不得新增台词、口号或解释性旁白。",
      ].join("\n"),
    },
  ];
}

export function buildDirectorMessages(
  context: GenerationContext,
  facts: SourceFacts,
  acceptedBody: string,
  task: StoryboardTask,
): ChatMessage[] {
  const durationProfile = getDurationProfileFromSnapshot(context.kbSnapshot, context.targetDuration);
  const taskQueue = task.task_queue.length > 0
    ? task.task_queue.map(
        (item, index) =>
          `- 片段 ${index + 1}: ${item.title} / ${item.allocated_duration_seconds} 秒 / ${item.source_label}\n  fragment: ${item.script_fragment}`,
      )
    : [`- 单任务片段 / ${task.target_duration_seconds} 秒 / ${task.task_source_label}\n  fragment: ${task.script_fragment}`];
  return [
    {
      role: "system",
      content: [
        "你是 Hope Web 的导演组。",
        "accepted body 是唯一事实源，task fragment 只是当前镜头任务的聚焦片段。",
        "返回严格 JSON，不要解释，不要 markdown。",
      ].join("\n"),
    },
    {
      role: "user",
      content: [
        `scene_type_id: ${context.sceneTypeId}`,
        `scene_type_label: ${context.sceneTypeLabel}`,
        `target_duration_seconds: ${context.targetDuration}`,
        `target_shot_count: ${durationProfile.targetShotCount}`,
        `director_summary: ${context.kbSummary.kb_context_summary}`,
        `scene_profile: ${context.kbSummary.scene_profile}`,
        "director_group_rules:",
        ...ruleLines(context.kbSummary.director_group_rule_pack_ids, context.kbSnapshot),
        "negative_constraints:",
        ...safePromptPayloadLines(context.kbSummary.negative_constraints).map((item) => `- ${item}`),
        "local_source_facts:",
        summarizeFacts(facts),
        "accepted_body_locked:",
        acceptedBody,
        "director_plan:",
        `split_reason_summary: ${task.director_plan.split_reason_summary}`,
        `prompt_guidance_summary: ${task.director_plan.prompt_guidance_summary}`,
        `duration_plan_summary: ${task.duration_allocation_plan.duration_plan_summary}`,
        "rows_seed:",
        ...task.duration_allocation_plan.allocations.map((item) => {
          const beat = task.duration_allocation_plan.beats.find((candidate) => candidate.beat_id === item.beat_id);
          return `- row ${item.row_index}: beat_id=${item.beat_id}; duration=${item.allocated_duration_seconds}s; role=${beat?.semantic_role ?? ""}; reason=${item.reason}; source_span=${beat?.source_span_ref ?? ""}; summary=${beat?.source_text_summary ?? ""}`;
        }),
        "task_queue:",
        ...taskQueue,
        "current_task_fragment:",
        task.script_fragment,
        "输出要求：",
        "- 输出 JSON 对象，字段 rows 为数组。",
        "- 每条 row 必须包含 shot_index, person, shot_size, camera, visual_description, character_action, dialogue_or_narration, duration_seconds, status, note。",
        "- rows 必须逐条覆盖 rows_seed；不要少行、漏行、跳号或只生成前半段。",
        "- rows 数量必须等于 rows_seed 数量；不要为了凑表格新增镜头，也不要沿用全局目标时长拆分当前镜头任务。",
        "- duration_seconds 必须直接使用对应 rows_seed 的 duration；所有 rows 的 duration_seconds 总和必须严格等于 target_duration_seconds。",
        "- 不允许少时长伪成功；无法覆盖目标时长时返回无法通过校验的 rows，不要编造完成。",
        "- visual_description 只写当前镜头可见画面。",
        "- person 必须来自 accepted body 中真实存在或明确可归属的人物/角色标签。",
        "- character_action 的动作主体必须与 person 字段一致；不要 person 写苏瑶但动作只写追兵，也不要 action 写守卫但 person 缺少守卫或对应角色标签。",
        "- dialogue_or_narration 只能使用 accepted_body_locked 或 current_task_fragment 中明确存在的对白/旁白；原文有明确对白时优先保留；没有依据时写“无”。",
        "- 不得新增台词、口号、解释性旁白、环境音拟写或心理独白。",
        "- camera 只写主运镜、方向和目的；不得写焦段、mm、镜头器材、三脚架、手持/肩扛制作术语或把景别塞进 camera。",
        "- prompt_text 可以留空，PWA 会按最终字段重新编译；如果输出 prompt_text，也不得包含内部治理、规则、校验或制作参考术语。",
        "- 不得输出内部来源资料、知识库原文、调试结构、规则标识或校验痕迹。",
      ].join("\n"),
    },
  ];
}

export function compilePromptText(
  row: Omit<StoryboardRow, "prompt_text">,
  params: {
    acceptedBody: string;
    sceneLabel: string;
    sceneProfile: string;
    durationPacing: string;
    directorSummary: string;
    negativeConstraints: string[];
  },
): string {
  void params.acceptedBody;
  void params.directorSummary;

  const visual = cleanPromptLine(row.visual_description, "当前镜头可见空间、人物站位和动作状态保持清晰。");
  const action = cleanPromptLine(row.character_action, "人物以可见动作和表情推进当前镜头。");
  const dialogue = cleanPromptLine(row.dialogue_or_narration, "无");
  const camera = cleanCameraPromptLine(row.camera, "固定机位");
  return [
    `主体：${cleanPromptLine(row.person, "待补充人物")}`,
    `画面：${visual}`,
    `动作：${action}`,
    `运镜：${camera}`,
    `景别：${cleanPromptLine(row.shot_size, "中景")}`,
    `对白旁白：${dialogue}`,
    `时长：第 ${row.shot_index} 镜 ${row.duration_seconds} 秒`,
    `镜头节奏：${userFacingPacing(params.durationPacing)}`,
    `风格：${params.sceneLabel}动漫分镜风格，保持当前镜头可见内容。`,
    `画面约束：${userFacingVisualConstraint(params.sceneLabel)}`,
  ].join("\n");
}
