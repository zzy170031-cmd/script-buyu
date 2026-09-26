# 不语剧本创作 Skill

**写故事、写剧本，完善人物、对白和前后逻辑；确认后交付对应的两表Excel脚本。**

名称：`script-buyu` · 调用：`$script-buyu` · 安装目录：[skills/script-buyu](skills/script-buyu)

核心是文本创作，面向AI漫剧等叙事需求。每部作品独立选择题材、结构、语言、节奏和画风，不固定科幻、现实玩家加游戏沙盘或参考稿的样式。

**[阅读完整功能简介](docs/Skill功能简介.md)**：包含全部功能、26类核心题材与31个组合入口、专家和资料数量口径、交付格式、工具及使用示例。整理日期：2026-09-26，功能依据版本1065925。

## 可以做什么

|功能|用途|
|---|---|
|故事创作与扩写|从想法、梗概或素材写成完整故事、分集及逐场正文|
|改编与局部修订|忠实改写或授权扩写，保留不可改事项，按单句/单场/单集/全季范围工作|
|人物与关系|写欲望、处境、选择、代价、成长、关系变化及群像|
|台词与情绪|改善接话、人物声音、潜台词、拒绝、幽默、重复、沉默及情绪余波|
|题材与专业研究|按当前题材选择方法，核历史、现实、职业或游戏版本规则|
|作家、导演与网文方法|按具体问题选用有来源的方法，辅以代表作品分析和电影学院公开教学资料|
|节奏与情绪回报|处理开场看点、持续推进、铺垫和爽感，保留必要喘息，不固定反转配额|
|导演式文本组织|写清动作、空间、声音事件、人物知情、信息揭示和场面节奏|
|统稿与连续性|唯一当前正文、明确统稿；检查时间、物件、伤势、能力、承诺、伏笔和跨场依赖|
|版本恢复与文本试读|以用户新来稿为准，比较前后稿及未结问题，检验具体修订是否成立|
|人物提示词与参考图|按本剧设计人物，先少量文外示例，确认方向后批量生成并逐人核对|
|DOCX与两表Excel|剧本确认稿、确认后分镜脚本和人物提示词/内嵌图|
|内置资料检索与校验|离线查询方法、写作知识和图像提示词，核结构、来源状态及资料完整性|

详细入口：[专业支持](skills/script-buyu/references/genre-professional-support.md) · [台词核心](skills/script-buyu/references/dialogue-craft.md) · [导演文本操作](skills/script-buyu/references/text-direction.md) · [唯一统稿](skills/script-buyu/references/ensemble-writing.md) · [连续性与恢复](skills/script-buyu/references/continuity-control.md) · [文本试读](skills/script-buyu/references/text-review.md)

## 从剧本到交付

1. 读取需求和来稿，明确题材、范围、背景及不可改项；必要时研究。
2. 完成人物、世界规则、分集与逐场正文，检查对白和连续性。
3. 交付含完整人物提示词、**不嵌人物图**的剧本DOCX；少量代表人物示例在文外展示。
4. 用户确认具体剧本及本剧视觉方向；同一条明确回复可完成两项确认。
5. 按已确认方向生成本次范围人物图，复用合格的同人物示例，交付真实XLSX。

|交付|内容|
|---|---|
|剧本DOCX|人物表：人物ID、姓名、人物设定、人物弧线、人物形象提示词；正文为完整逐集逐场故事|
|Excel Sheet1|镜号、场景、人物、动作描述、主画面描述、运镜、台词；一镜一行|
|Excel Sheet2|人物ID、人物姓名、人物形象提示词、人物参考图；图片实际内嵌并逐人对应|

正式成品是DOCX与XLSX两份，人物示例是中间预览。局部修订或诊断按用户指定范围交付。全稿无人且没有身份明确的画外角色时，不造人物、不生人物图，文本确认后Sheet2保留空表头。

已确认内容保护原台词/旁白、人物、事件、因果、结果和揭示顺序；重复发言按每次发生分别保留。修改只重新处理受影响确认，不借运镜、图片或方法切换改剧情。详见[输出规范](skills/script-buyu/references/output-contract.md)、[人物形象](skills/script-buyu/references/character-visuals.md)与[Excel交付](skills/script-buyu/references/storyboard-excel.md)。

## 方法与内置资料

|资料|当前登记或快照|
|---|---|
|题材导航|26核心题材、31组合入口；可扩展，组合不另算独立专家池|
|JSON人物与方法|156名自然人（16基线＋140新增），199条来源、209项方法；26类共291条绑定|
|对白支持|12种技巧、24场景入口、16情绪入口、8个研究入口（含1待补证候选）、12组原创示例|
|中文网文方法|18位已读方法来源入口，另保留未核候选，不与JSON人物数直接相加|
|学院参考|AFI、USC、UCLA TFT、NFTS的4张公开教学资料适配卡|
|写作知识|152条黄金库记录、149条craft、25篇wiki；黄金库含97未审候选、11负例、44储备|
|来源副本|Hope KB 114文件、Hope Web PWA 11文件；外部编剧18模块适配与54项相关原始节选|
|图像提示词|11类、22,744分类记录；15,127唯一ID、14,831段不同全文；示例图为来源链接|

核心题材当前标准是**作家与导演合计至少10位不同新增人物且两类都有**，不是两类各十人。人物为公开方法来源，不代表真人参与或背书；学院不计自然人。“黄金”为上游库名，不表示全部是已验收优秀剧本。

资料已放在Skill目录内，无需另外安装来源Skill。正文、来源归档和候选状态分开，普通创作不执行上游命令或自动更新资料。图像数量为固定快照实测口径，非实时上游规模。详见[内置资料与许可边界](skills/script-buyu/references/bundled-sources.md)、[知识库](skills/script-buyu/references/knowledge-library.md)、[题材方法](skills/script-buyu/references/genre-methods.md)、[网文方法](skills/script-buyu/references/dialogue-webnovel.md)。

## 如何使用

将本仓库的`skills/script-buyu`完整目录安装到宿主支持的Skill位置，或使用可用的Skill安装器。仅克隆仓库不会自动全局安装。

> 使用 $script-buyu。根据我的想法写完整分集剧本，按故事选择题材、结构和语言。DOCX保留人物提示词，不嵌图；文外先展示少量代表人物示例。

> 使用 $script-buyu。只修这一场对白，增强人物差异与接话，保留已定决定、关系及后场事件；其他问题指出位置，不改全篇。

> 这版剧本与示例视觉方向均已确认。按获批范围生成对应人物图并交付两表Excel，保持原话、事件和揭示顺序。

用户不需要编写JSON，也不需要填写内部专家记录。Word中的真实新修改优先，旧JSON不能覆盖新正文。

## 工具与运行条件

写作、研究和判断由调用Skill的Agent完成；内置Python脚本用于检索、文档读写与校验，不自动代写故事。DOCX脚本使用Python 3.10+、`python-docx>=1.1,<2`。联网检索、生图、XLSX写入/嵌图和渲染依赖宿主工具；没有独立内置的XLSX生成器。

从仓库根目录运行：

```text
python skills/script-buyu/scripts/query_methods.py --list-genres
python skills/script-buyu/scripts/query_methods.py --genre 悬疑 --query "证据 揭示" --limit 3
python skills/script-buyu/scripts/query_knowledge.py --query "对白" --limit 3
python skills/script-buyu/scripts/query_image_prompts.py --query "人物 portrait character" --limit 3
python skills/script-buyu/scripts/read_source_docx.py --input inputs/source.docx --output work/source-read.json
python skills/script-buyu/scripts/generate_story_docx.py --input work/screenplay.json --output deliverables/story-v1.docx
python skills/script-buyu/scripts/extract_story_docx.py --input deliverables/story-v1.docx --output work/revised-story.json
python skills/script-buyu/scripts/compare_story_versions.py --before work/old.json --after work/new.json
python skills/script-buyu/scripts/validate_skill.py
python skills/script-buyu/scripts/verify_knowledge.py
python -m unittest discover -s skills/script-buyu/tests -v
```

完整工具说明见[功能简介](docs/Skill功能简介.md)。旧Word嵌图脚本只作兼容，不进入当前默认流程。生成器保留旧文件；未知Word结构及渲染限制需如实说明，不能把拒绝导入当作内容为空。

## 验证与维护

最近的文本补强验证包含43项针对性检索/差分测试及三个短文本试用；首次试用的一处信息精度问题和定点修正均保留原件。详见[文本创作补强与验证](docs/文本创作补强与验证.md)。这些证据不等于全仓库测试、全季可靠性或文学质量保证。

本Skill服务文本创作和约定的人物图辅助，不扩展为场景批量生图、试拍、配音、视频制作、模型训练或生产系统；不承诺爆款、精确成片时长或永不出现剧情错误。

研究与维护记录：[连续性补强](docs/剧情一致性补强研究与验证.md) · [台词接入](docs/台词能力接入记录.md) · [历史作家导演卡清单](docs/作家导演卡完整清单.md) · [题材人物目录](docs/题材与人物全目录.md) · [独立安装历史验证](docs/独立安装与内置资料验证.json) · [来源维护](skills/script-buyu/references/source-sync.md)。历史资料保留各自快照与验证范围；当前操作以[Skill入口](skills/script-buyu/SKILL.md)、引用的参考页与数据为准。
