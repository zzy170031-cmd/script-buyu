# 不语剧本创作 Skill

专门创作、扩写、改编和修订故事剧本。先交付含完整人物提示词、不嵌人物图的DOCX，在文档外展示少量代表人物示例；用户确认剧本及本剧视觉方向后，批量生成人物图并交付Excel：Sheet1七列分镜脚本，Sheet2完整人物提示词与内嵌图。每部作品独立选择画风、题材和结构，不固定现实玩家与游戏沙盘的形式。

## 能力边界

来稿与背景研究 → 人物及完整逐场故事 → 含人物提示词的DOCX＋文外少量人物示例 → 剧情与视觉方向确认 → 批量生成本次范围全部人物 → 分镜改编与逐人嵌图 → 两张工作表的XLSX。

默认面向AI漫剧，加入 [观看节奏与情绪回报](skills/script-buyu/references/audience-rhythm.md)：开场看点、持续推进和有铺垫的回报，按作品选择智谋、实力、关系、幽默或奇观等体验，不统一套用打脸和反转。保留人物对立、人物弧线、不同题材的表现方法、现实与虚拟世界的因果穿插、分集标注、时长预算及修订回读。具体主角、游戏、集数、比例和时长都由当前用户需求确定，不预置旧项目。

**本仓库服务剧本与分镜脚本。** Word人物表第五列仅放完整提示词；少量人物示例在文档外直接展示，不先生成全员。用户可用同条回复确认剧情和视觉方向，不再追加生成许可。合格的同人物示例可复用，其他角色确认后生成。Excel保持七列分镜及第二表人物提示词／图片；范围不扩展到场景批量生图、模型配置或实际视频制作。历史样本只说明格式和质量，不固定风格。

核心评价是文本能否让读者理解行动、相信人物并感受到情绪。[全题材专业支持](skills/script-buyu/references/genre-professional-support.md) 将26类现有作家/导演方法与项目所需的专业研究职责连接；专业意见由唯一主笔/统稿取舍，不能替角色决定剧情。[导演文本操作](skills/script-buyu/references/text-direction.md) 处理空间、动作、声音与知情，[文本试读](skills/script-buyu/references/text-review.md) 核验具体修订，不要求试拍、配音或成片测试。

本次补强及实际文本样本的验证范围见 [文本创作补强与验证](docs/文本创作补强与验证.md)；程序通过、有限试用与长期写作效果分别记录。

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

历史整合记录见 `docs/J20-整合审计.md` 和 `docs/J10-剧本到脚本流程审查.md`。默认流程及前期方法库研究见 [示例确认与创作方法J10](docs/J10-示例确认与创作方法审查.md) 和 [作家导演方法接入方案](docs/作家导演方法接入方案.md)。此前五项研究方案扩充成14张可选方法卡，接入 [按场景选法与整剧一致性](skills/script-buyu/references/scene-methods.md)。此前十四卡扩充未另开J10，不能借原报告扩大审查范围；六类首批及本轮题材补全分别有独立J10记录。程序、只读审查、实际写作及视觉验收各有证据边界，不相互替代。

## 题材与专业方法

逐卡阅读见 [作家导演卡完整清单](docs/作家导演卡完整清单.md)：两轮新增140位创作者、182张方法卡，含逐人索引、全部方法步骤与来源，另附原有17项公开方法。作家/编剧类59张、导演类59张、兼任类64张按单卡来源职责分类；学院参考不计入人物卡。此清单供人工查阅，Skill执行时仍按题材和问题有界检索，避免整库注入。

现有26个核心题材均有作家与导演合计至少10位不同自然人的来源适配，覆盖两类职责；另有31个组合入口，供谍战、末世、宫斗、医疗、法律、赛博朋克等交叉选用。组合入口不是另造十人池。完整名单、作品、来源和逐类用途见 [题材与人物全目录](docs/题材与人物全目录.md)，按 [题材检索入口](skills/script-buyu/references/genre-methods.md) 有界读取。

本轮在六类首批基础上新增93人、134张卡；累计相对原始基线新增140人。库内共199份来源记录、199项公开来源适配方法及10项内部规则，26类有291个逐类绑定。同人多作品不重复算人，同一采访中的不同发言不冒充独立来源。185个规范URL容器也不等于185份独立上游证据；转载需人工识别。材料包含本人讲解与3项明确标记的原作段落分析。

另加入 [代表作品与电影学院资料](skills/script-buyu/references/academic-methods.md)：AFI、USC、UCLA TFT、NFTS的4张教学文本适配卡。依据是已读官方公开课程简介或学习目标，没有声称学完整门课，也没有学院背书。机构不计自然人。按作品、场景问题选法，不按名气、人物数量或一套固定风格分配正文。

为防同段多人拼贴、抢戏和前后断裂，新增 [唯一统稿与一致性](skills/script-buyu/references/ensemble-writing.md)：唯一当前正文、明确统稿责任、建议采纳/改造/弃用、人物因果职能和知情/伤势/道具/伏笔依赖检查。可看 [问题稿与修复演练](docs/多方法统稿一致性演练.md)。群像允许多线并重，节奏允许留白与余波；不按台词份额分配戏份。

本轮资料、流程和检索边界审查见 [J10扩展记录](docs/J10-题材补全与多方法一致性审查.md)。方法、资格与可定位来源支持研究和选择，不证明文学质量、平台留存或最终成片效果；实际应用必须指向当前正文的修改或检查结果。新增134张卡只用于草稿或获授权修订；已确认内容继续受DOCX→两表Excel边界保护。

## 台词与整剧表达

[台词核心](skills/script-buyu/references/dialogue-craft.md)已接入写作第4步：先写完整互动，按实际缺陷调用12种修订方法、24种场景入口、16种情绪入口、8张作家/导演研究卡和12组原创示例。题材导航沿用26类与31条复合路线，可继续扩展，不固定口吻或故事结构。

[网文方法](skills/script-buyu/references/dialogue-webnovel.md)含18位有已读方法来源的作家入口，覆盖番茄、起点及其他中文连载经验；其中本次追加我会修空调、卖报小郎君、狐尾的笔、老鹰吃小鸡、耳根、远瞳、吴半仙、御井烹香、囧囧有妖、桉柏10位。来源自述与本项目应用分开；白鹭成双、弈青锋另列待核，WM03 Fosse也保持候选，不计作已核可用方法。

本批DL/SC/EM/WM/WN是按Markdown入口读取的支持资料，未写入旧JSON人物库，数量不与上面的199份来源或人物数相加；query_methods.py不检索本批卡。采用同一统稿职责整合方法，保护知情、决定权、伏笔、语气与情绪余波，已确认台词继续按原文发生位置核对转Excel。接入范围及实际验证见[台词能力接入记录](docs/台词能力接入记录.md)。

## 剧情连续性与版本修订

[剧情状态与恢复](skills/script-buyu/references/continuity-control.md)接入主流程：保存当前源与确认范围，区分故事事实、人物信念、观众信息和未来计划；修改后既追已知依赖，也回读正文查漏，恢复任务时先核新来稿与未结项。内部记录不会进入两份用户交付。

新增只读工具 `compare_story_versions.py` 比较前后结构化剧本，列出同revision内容变化、角色/事实/台词变化和发生顺序；它不判定语义、不自动确认，也不读取Excel。确认后分镜要求源稿与实际XLSX双向对应，并检查动作/画面是否偷偷改变因果与揭示。六份一手资料的已读范围、采用方法与限制见[研究依据](skills/script-buyu/references/continuity-research.md)，行为验证见[评测办法](skills/script-buyu/references/continuity-evaluation.md)。这些措施帮助检查具体错误，不构成无错误保证。本轮接入和实测范围见[补强研究与验证](docs/剧情一致性补强研究与验证.md)。

## 来源与拆分说明

Hope KB与Hope Web PWA实际使用的内容已复制进本Skill的`references/source-archive/`，分别114和11个文件；版本、逐文件哈希与去向可查 [内置资料说明](skills/script-buyu/references/bundled-sources.md)。只安装`skills/script-buyu`也包含这些资料，写作检索不依赖另外两个项目的位置或服务。

此前采用的screenwriting-skills已有18模块本地写作适配，并补入54项相关原始检查表、工作步骤或分析索引的本地节选；YouMind图像提示词保存可离线查询的全文快照。来源、版本、许可和使用入口一并列入上述说明。无需另外安装这些来源Skill；外部URL用于溯源，公开原书及上游示例图片不冒充已完整内置。

此前已将Skill目录单独复制测试：94项回归、资料完整性、六组实际查询和官方Skill结构校验均通过，当时验证的参考链接均在Skill内部；本次文档增补另见台词能力接入记录。详见 [独立安装与内置资料验证](docs/独立安装与内置资料验证.json)；该记录验证打包及工具可用性，不代替真实剧本与人物图片的内容验收。

原版从用户授权的 `ai-buyu` 项目中抽取故事分析、研究边界、完整剧本与可见正文回读原则。本次整合 Hope KB 和 PWA 的写作相关内容，保持单目录自包含，不依赖其他仓库安装。未复制用户私人故事正文或人物画像提示词。

新增资料入口见 [知识库用法](skills/script-buyu/references/knowledge-library.md)、[输出规范](skills/script-buyu/references/output-contract.md) 和 [来源清单](skills/script-buyu/data/source-manifest.json)。

- Hope KB 内容来自 `codex/contracts-freeze` 分支 `7212eb6168fce040f593e5629e8a9275b9f358f4`；main 只有框架。
- 当前种子库 152 条黄金记录；V108 原始工作簿/说明、115 条历史规范化记录、早期 CSV/40 条记录保留溯源，版本重叠不相加。
- 收录 149 条可检索写作及相邻连续性记录、25 篇相关 wiki、21 类场景导航；PWA 83 个规则包有逐项写作适配或仅归档去向。
- 联网检索 [screenwriting-skills](https://github.com/jtydhr88/screenwriting-skills)，将 18 个模块的方向适配为按需中文编剧方法，其他专项保留取舍。上游 MIT 只覆盖原创内容，LICENSE/NOTICE 随库保存，不复制整套出版书籍及剧本引文。

“黄金”是上游库名，负例、储备和候选状态保留，未宣称全部已被独立验收为优秀剧本。PWA 的 prototype/partial 和源占位 hash 也不被提升为正式通过。原始混合资料仅被动归档，生产字段不成为本技能的操作能力。

知识更新是维护任务，遵循 [同步说明](skills/script-buyu/references/source-sync.md)，普通创作不自动同步、安装或发布。克隆或修改仓库不代表已全局安装或推送。
