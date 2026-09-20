# 不语剧本创作 Skill

从故事梗概或已有文档，产出可阅读、可修订的完整动画或漫剧故事剧本。默认只交付一个 DOCX，交付后停止，等待用户确认或修改。

## 能力边界

来稿完整阅读 → 输入与题材判断 → 按需核实背景和参考案例 → 编剧职责协作 → 人物与故事设定 → 分集规划 → 逐场动作与对白 → 剧本检查 → DOCX。

保留人物对立、人物弧线、不同题材的表现方法、现实与虚拟世界的因果穿插、分集标注、时长预算及修订回读。具体主角、游戏、集数、比例和时长都由当前用户需求确定，不预置旧项目。

**本仓库止于故事剧本。** 不输出人物画像提示词、参考图生成任务、分镜、运镜、镜头合同、模型参数、图像或视频生成提示词、制作 JSON、Excel。用户提供带这些内容的混合文档时，只把它们作为输入资料辨识；不静默丢弃，也不直接带入本 Skill 的输出。

这是一套供 AI Agent 使用的 Skill，不是网页前端，也不是独立调用模型的服务。创作与联网检索由调用它的 Agent 完成；Python 工具只负责文档读取、结构验证、排版与回读，不会把梗概自动变成剧本。

## 使用

Skill 位于 `skills/script-buyu`，名称为 `$script-buyu`。通过可用的 Skill 安装器安装该仓库的这个目录，或把完整目录放到宿主支持的 Skill 位置。仅克隆仓库不会自动安装到全局。

调用示例：

> 使用 $script-buyu。根据我提供的故事文档创作完整分集故事剧本，保留核心人物和背景。先分析题材与事实边界，写清人物对立和逐场动作对白，最终给我一个 DOCX 待确认，不要生成镜头或提示词。

用户不需要编写 JSON。内部 `screenplay.json` 是 Agent 的工作数据，不是默认交付件。用户在 Word 中的修改必须以实际可见正文为准，不能被旧 JSON 覆盖。

## 运行与测试

Python 3.10+，依赖 `python-docx>=1.1,<2`；无模型 API、无下载脚本、无自动发布动作。请使用当前环境允许的依赖运行时，缺包时明确报告，安装需遵守宿主权限。

```text
python skills/script-buyu/scripts/read_source_docx.py --input inputs/source.docx --output work/source-read.json
python skills/script-buyu/scripts/generate_story_docx.py --input work/screenplay.json --output deliverables/story-v1.docx
python skills/script-buyu/scripts/extract_story_docx.py --input deliverables/story-v1.docx --output work/revised-story.json
python skills/script-buyu/scripts/validate_skill.py
python -m unittest discover -s skills/script-buyu/tests -v
```

生成器对已有路径拒绝覆盖。提取器只自动解析本 Skill 自己的格式；未知表格、未处理修订、图片或文本框会要求 Agent 完整核对，不把提取失败解释为“内容为空”。普通外部 DOCX 先用读取器展开资料，再由 Agent 整理。

DOCX 需要在可用的文档渲染器中逐页检查；程序结构通过不等于排版或编剧质量通过。当前仓库的测试是公开的原创微型故事和边界测试，不代表任何用户项目已确认。

2026年9月20日本地验证：47项回归测试及仓库自带结构检查通过。宿主官方快速检查因缺少 PyYAML 未完成，DOCX 页面渲染因缺少宿主配套 LibreOffice 未完成；不能据此宣称视觉排版已验收。当前发布的是可检查、可继续测试的 Skill 源码，不附已经视觉验收的示例成稿。实际调用仍需 Agent 执行创作评审和排版检查。

## 专家资料的真实边界

`data/story-methods.json` 包含少量已读取一手来源支持的公共方法，以及明确标为本库编写规则的操作检查。`data/expert-candidates.json` 保留原系统的12个故事创作候选检索入口，未重新核实的个人方法不进入已证实专家数量。选用时必须读来源并建立“方法 → 具体场景/字段 → 修改或检查结果”的记录。

这些资料不代表真人参与、授权或代写，不证明10–15人专家组已经全部具备专业资格，也不承诺每次调用都能生成顶级作品。编剧角色是工作职责，真实专家姓名只用于准确归属公开方法。

## 来源与拆分说明

从用户授权的 `ai-buyu` 项目中抽取故事分析、领域贴合、研究边界、完整剧本与可见正文回读原则；重新隔离运行代码，不依赖该项目本地路径、后续制作模块或 hope-kb 的安装。未复制私人故事、图片和研究日志。

打包结构参考 [OpenAI 官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)。方法出处和当前证据限制随资料保存。第三方网页仅链接和简述，不附原文、剧照或受保护的样板剧本。本次没有新增第三方材料的授权声明。
