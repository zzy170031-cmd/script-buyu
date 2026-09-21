# 已内置的外部 Skill 写作资料

本Skill已经保存实际使用的Hope KB与Hope Web PWA资料副本。普通创作读取自身目录内的文件，不需要再安装这两个Skill、不需要原项目目录或它们的在线服务。原始来源URL及提交只用于溯源，当前冻结版本不等于上游永远没有新内容。

此前采用的外部编剧Skill方法和图像提示词也有本地内容，见下表。参考来源属于资料，不是需要再次安装或在运行时调用的上游Skill；执行统一服从本Skill的故事范围与确认流程。

| 来源 | 固定提交 | 本Skill内的实际副本 |
| --- | --- | --- |
| hope-kb，内容分支codex/contracts-freeze | 7212eb6168fce040f593e5629e8a9275b9f358f4 | [114个归档文件](source-archive/hope-kb/) |
| hope-web-pwa | a875b02449b1f1dba0209ba7274def91feccb225 | [11个归档文件](source-archive/hope-web-pwa/) |
| jtydhr88/screenwriting-skills | 50825325b3940a17f032129851f5c83382863000 | [18模块的中文写作适配正文](external-screenwriting.md)、[逐模块映射](../data/external-skill-map.json)、[LICENSE](source-archive/external/LICENSE)与[NOTICE](source-archive/external/NOTICE) |
| YouMind-OpenLab/ai-image-prompts-skill | f06c94d36a4194f881c2d27063b418ea78a99896 | [图像提示词数据](../data/image-prompts/)、[快照清单](../data/image-prompts/snapshot.json)；11类22,744分类记录，15,127唯一ID及14,831不同提示词全文 |

编剧模块已有可直接阅读使用的本地方法正文，外部URL仅用于核实来源。上游混有出版书籍、剧本和译文摘录；当前内置的是相关写作方法适配，不把未获同等许可的引文全集或跨Skill执行指令整体搬入。图像库保留提示词全文、来源与MIT许可，示例图片仍为链接；人物参考图按本剧需求和确认流程生成，不要求下载上游示例图才能检索提示词。

逐文件来源、用途、固定版本和SHA-256见 [来源清单](../data/source-manifest.json)。已包含用于阅读溯源的原始表格/文档、规范化资料、写作与样本说明、PWA相关规则文件；无需到原仓库才能打开索引命中的资料。未收录的应用代码、治理和纯制作资料有取舍记录，不参与当前写作。

工作入口均在Skill内：

- [知识索引](../data/knowledge-index.json)：152条黄金记录、149条写作及相邻连续性记录、25篇wiki。历史版本重叠不叠加人数/样本数；来源标签不代表本次故事质量已验收。
- [PWA规则映射](../data/rule-crosswalk.json)：保留写作适配与只归档的区别，不能把原项目生产要求变成试拍/视频制作流程。
- [场景目录](../data/scene-catalog.json)：按当前题材及场景问题选取，避免继承旧项目固定人物、画风和结构。
- [本库人物方法](../data/story-methods.json)、[题材索引](../data/genre-index.json)：作家导演方法及资格、出处、适用限制可离线检索；学院资料见 [教学文本适配](academic-methods.md)。

检索前执行`python scripts/verify_knowledge.py`可核对归档文件、索引定位、内容投影与目录边界；`query_knowledge.py`也会执行该检查。缺失或失配时停止提供该批知识结果，不把缺文件解释成没有相关内容。维护更新才按 [来源同步规则](source-sync.md) 检查上游；普通写作不自动联网同步或执行档案命令。

自包含指本Skill所用写作资料和脚本均有本地副本；实际创作、联网研究、人物生图和文档导出仍使用宿主提供的模型、工具与 [声明的Python依赖](../requirements.txt)。不额外携带原项目服务、视频生成或自动发布流程。
