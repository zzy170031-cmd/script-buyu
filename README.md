# 不语剧本创作 Skill

专门创作、扩写、改编和修订故事剧本。先交付含完整人物提示词、不嵌人物图的DOCX，在文档外展示少量代表人物示例；用户确认剧本及本剧视觉方向后，批量生成人物图并交付Excel：Sheet1七列分镜脚本，Sheet2完整人物提示词与内嵌图。每部作品独立选择画风、题材和结构，不固定现实玩家与游戏沙盘的形式。

## 能力边界

来稿与背景研究 → 人物及完整逐场故事 → 含人物提示词的DOCX＋文外少量人物示例 → 剧情与视觉方向确认 → 批量生成本次范围全部人物 → 分镜改编与逐人嵌图 → 两张工作表的XLSX。

默认面向AI漫剧，加入 [观看节奏与情绪回报](skills/script-buyu/references/audience-rhythm.md)：开场看点、持续推进和有铺垫的回报，按作品选择智谋、实力、关系、幽默或奇观等体验，不统一套用打脸和反转。保留人物对立、人物弧线、不同题材的表现方法、现实与虚拟世界的因果穿插、分集标注、时长预算及修订回读。具体主角、游戏、集数、比例和时长都由当前用户需求确定，不预置旧项目。

**本仓库服务剧本与分镜脚本。** Word人物表第五列仅放完整提示词；少量人物示例在文档外直接展示，不先生成全员。用户可用同条回复确认剧情和视觉方向，不再追加生成许可。合格的同人物示例可复用，其他角色确认后生成。Excel保持七列分镜及第二表人物提示词／图片；范围不扩展到场景批量生图、模型配置或实际视频制作。历史样本只说明格式和质量，不固定风格。

用户提供的 [脚本提示词原文](skills/script-buyu/references/script-prompt-original.txt) 完整归档，按 [脚本与Excel交付规则](skills/script-buyu/references/storyboard-excel.md) 使用。保留细致动作、画面及运镜，玄幻、热血、三渲二等按本剧选择；不为“短促”改写已确认台词。剧情确认或视觉确认只完成其一时，不能提前批量人物图或正式Excel。

新增图像提示词资料来自 [YouMind-OpenLab/ai-image-prompts-skill](https://github.com/YouMind-OpenLab/ai-image-prompts-skill)，MIT 许可原文随数据保留。固定快照含11类、22,744条分类记录，实测15,127个唯一ID、14,831条不同提示词全文；上游清单标称15,670，与实测不一致，已记录。数据支持离线按题材检索，示例图片仅保留来源链接；上游脚本、自动同步与交互流程不执行。详见 `skills/script-buyu/references/character-visuals.md` 及 `data/image-prompts/snapshot.json`。

这是一套供 AI Agent 使用的 Skill，不是网页前端，也不是独立调用模型的服务。创作与联网检索由调用它的 Agent 完成；Python 工具只负责文档读取、结构验证、排版与回读，不会把梗概自动变成剧本。

## 使用

Skill 位于 `skills/script-buyu`，名称为 `$script-buyu`。通过可用的 Skill 安装器安装该仓库的这个目录，或把完整目录放到宿主支持的 Skill 位置。仅克隆仓库不会自动安装到全局。

调用示例：

> 使用 $script-buyu。根据我的故事文档写完整分集剧本，保留核心人物背景和逐场动作对白。按本剧内容选择画风，DOCX人物表放完整提示词、不嵌图，文档外先给少量代表人物示例供我确认。

> 这版第一集剧本和人物示例方向都确认了。按这个方向生成第一集全部人物图，再交付Excel：Sheet1分镜脚本，Sheet2人物提示词和内嵌参考图。

用户不需要编写 JSON。内部 `screenplay.json` 是 Agent 的工作数据，不是默认交付件。用户在 Word 中的修改必须以实际可见正文为准，不能被旧 JSON 覆盖。

## 运行与测试

DOCX 辅助脚本使用 Python 3.10+，依赖 `python-docx>=1.1,<2`；无模型 API、无下载脚本、无自动发布动作。Excel 由 Agent 使用宿主允许的表格工具创作、嵌图、导出、回读和渲染；现有 Python 剧本工具不冒充 XLSX 生成器。缺少对应能力时如实报告，安装需遵守宿主权限。

```text
python skills/script-buyu/scripts/read_source_docx.py --input inputs/source.docx --output work/source-read.json
python skills/script-buyu/scripts/generate_story_docx.py --input work/screenplay.json --output deliverables/story-v1.docx
python skills/script-buyu/scripts/extract_story_docx.py --input deliverables/story-v1.docx --output work/revised-story.json
python skills/script-buyu/scripts/validate_skill.py
python skills/script-buyu/scripts/query_knowledge.py --query "对白" --limit 3
python skills/script-buyu/scripts/verify_knowledge.py
python -m unittest discover -s skills/script-buyu/tests -v
```

生成器拒绝覆盖旧文件。新人物数据为全员填写 `visual_prompt`，生成五列纯文字人物表并严格回读完整提示词；旧四列仍兼容。未知表格、未处理修订、图片或文本框需完整核对，不把失败解释为内容为空。旧含图稿用通用读取器，原嵌图工具只保留旧格式兼容，不在新默认路线运行。

DOCX 需要在可用的文档渲染器中逐页检查；程序结构通过不等于排版或编剧质量通过。当前仓库的测试是公开的原创微型故事和边界测试，不代表任何用户项目已确认。

历史整合记录见 `docs/J20-整合审计.md` 和 `docs/J10-剧本到脚本流程审查.md`。新默认流程及方法库研究见 [本次J10](docs/J10-示例确认与创作方法审查.md) 和 [作家导演方法接入方案](docs/作家导演方法接入方案.md)。此前五项研究方案现已扩充为14张可选方法卡，接入 [按场景选法与整剧一致性](skills/script-buyu/references/scene-methods.md)。本次扩充不是一次新的J10审计，原报告仅证明当时范围。程序、只读审查、实际写作及视觉验收各有证据边界，不相互替代。

## 专家资料的真实边界

`data/story-methods.json` 现含17项有公开来源支持的方法（原3项＋新增14项）及10项本库编写规则。来源记录区分直接阅读、官方搜索正文和采访转载，部分原页访问受限；不把链接存在当作全文已读。新增涵盖观察、对白、口述、科幻、群像、喜剧、悬念、空间、多线时间、留白、心理意象与动作；按场景需要调用，统筹回查整剧。`data/expert-candidates.json` 保留原系统的12个故事创作候选检索入口，未重新核实的个人方法不进入已证实专家数量。选用时必须读来源并建立“方法 → 具体场景/字段 → 修改或检查结果”的记录。

这些资料不代表真人参与、授权或代写，不证明10–15人专家组已经全部具备专业资格，也不承诺每次调用都能生成顶级作品。编剧角色是工作职责，真实专家姓名只用于准确归属公开方法。

## 来源与拆分说明

原版从用户授权的 `ai-buyu` 项目中抽取故事分析、研究边界、完整剧本与可见正文回读原则。本次整合 Hope KB 和 PWA 的写作相关内容，保持单目录自包含，不依赖其他仓库安装。未复制用户私人故事正文或人物画像提示词。

新增资料入口见 [知识库用法](skills/script-buyu/references/knowledge-library.md)、[输出规范](skills/script-buyu/references/output-contract.md) 和 [来源清单](skills/script-buyu/data/source-manifest.json)。

- Hope KB 内容来自 `codex/contracts-freeze` 分支 `7212eb6168fce040f593e5629e8a9275b9f358f4`；main 只有框架。
- 当前种子库 152 条黄金记录；V108 原始工作簿/说明、115 条历史规范化记录、早期 CSV/40 条记录保留溯源，版本重叠不相加。
- 收录 149 条可检索写作及相邻连续性记录、25 篇相关 wiki、21 类场景导航；PWA 83 个规则包有逐项写作适配或仅归档去向。
- 联网检索 [screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills)，将 18 个模块的方向适配为按需中文编剧方法，其他专项保留取舍。上游 MIT 只覆盖原创内容，LICENSE/NOTICE 随库保存，不复制整套出版书籍及剧本引文。

“黄金”是上游库名，负例、储备和候选状态保留，未宣称全部已被独立验收为优秀剧本。PWA 的 prototype/partial 和源占位 hash 也不被提升为正式通过。原始混合资料仅被动归档，生产字段不成为本技能的操作能力。

知识更新是维护任务，遵循 [同步说明](skills/script-buyu/references/source-sync.md)，普通创作不自动同步、安装或发布。克隆或修改仓库不代表已全局安装或推送。
