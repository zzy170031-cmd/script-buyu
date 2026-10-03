# 已审拉片资料：薄目录与精选分析

按当前写作问题选查。这里是资料入口，不增加创作步骤、专家层、确认门槛或输出要求，也不改变默认知识检索和黄金样本池。没有具体问题时可直接创作。

## 范围与状态

- [独立索引](../data/scene-study-index.json)：scene-study-portable/2，正式资料截点2026-10-03 01:52 UTC
- 正式登记1106父、来源通过1081父、至少一个目标批准1049父；31类各有至少51个正式批准父
- 随包薄目录1049父、697个归一出处，按当前获准标签可查；其中20父另有精简自有分析。完整薄目录不等于1049份完整场面正文或已实看片段，精选数也不代替正式覆盖数
- catalog只给作品/版本、批准标签、可读的审定短范围、主题、出处与审核定位；curated_analysis再给少量问题、分析和具体限制。短范围和主题词用于定位本例，不展开情节。辅助/待补只在status_only中保留状态，不进入正向查读
- 逐标签保留批准证据，不以另一标签自动扩大范围。别名沿同一父ID，不新增内容数。来源审核为模型完成的文字核验，不能冒充真人外审
- 本包继承已记录的局部文字阅读，没有重新联网；全库连续声画实看0、全片实看0。已有有限静图仅保留匹配范围，读文字不等于看成片。没有证明文学效果或方法迁移成功

索引SHA256：96bef0a0a07aa1d7a801f86f89bc15d0b53ae0ea9b3a31731df6a2f9bf8de6ae

## 查读

由Agent从当前Skill根目录执行下面的只读示例；宿主也可将相对路径解析到安装目录。使用系统已有Python标准库即可，无须另装依赖或让用户填写JSON。网络不是查读这份索引的前提；原文链接需要联网才能追源。

参数依次为：索引、catalog或analysis、题材（空字符串表示不限）、问题词或父ID/别名、条数、起始偏移。通常先取1–3项；盘点某题材时可以按返回的next_offset分页。analysis无命中仍可查catalog，薄目录无命中可换词或按作品/ID查，不等于不存在相关研究。

```text
python - data/scene-study-index.json analysis 武侠 礼仪 3 0 <<'PY_LOOKUP'
import hashlib, json, sys
from pathlib import Path
p, mode, genre, query, limit, offset = sys.argv[1:]
p = Path(p)
expected = "96bef0a0a07aa1d7a801f86f89bc15d0b53ae0ea9b3a31731df6a2f9bf8de6ae"
raw = p.read_bytes()
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit("可选资料校验不符；停用该资料，既有创作和原知识检索仍可继续")
d = json.loads(raw)
assert d["schema_version"] == "scene-study-portable/2"
assert mode in ("catalog", "analysis")
limit, offset = min(20, max(1, int(limit))), max(0, int(offset))
words = query.casefold().split()
cat = {r["case_id"]: r for r in d["catalog"]}
rows = d["catalog"] if mode == "catalog" else d["curated_analysis"]
def match(r):
    if genre and genre not in r["approved_genres"]:
        return False
    alias = cat[r["case_id"]].get("aliases", [])
    fields = [r["case_id"], alias, r["work_title"], r.get("scope_keywords", []), r.get("scope_labels", []),
              r.get("scene_scope", ""), r.get("topics", []),
              r.get("retrieval_questions", []), r.get("own_analysis", "")]
    text = json.dumps(fields, ensure_ascii=False).casefold()
    return not words or any(w in text for w in words)
matched = [r for r in sorted(rows, key=lambda r: r["case_id"]) if match(r)]
chosen = matched[offset:offset + limit]
proof_ids = {a["proof_id"] for r in chosen for a in r["tag_approvals"]}
proofs = [r for r in d["approval_proofs"] if r["proof_id"] in proof_ids]
source_ids = {s for r in chosen for s in r["source_ids"]}
source_ids.update(s for r in proofs for s in r["source_ids"])
review_ids = {r["review_id"] for r in proofs}
result = {"mode": mode, "total_matches": len(matched), "offset": offset,
          "next_offset": offset + len(chosen) if offset + len(chosen) < len(matched) else None,
          "boundaries": d["global_boundaries"], "records": chosen,
          "sources": [s for s in d["sources"] if s["source_id"] in source_ids],
          "approval_proofs": proofs,
          "review_provenance": [r for r in d["review_provenance"] if r["review_id"] in review_ids]}
output = json.dumps(result, ensure_ascii=False, indent=2)
if len(output) > 24000:
    raise SystemExit("完整结果超过显示预算；减少条数或按父ID查，不能截掉出处和限制")
print(output)
PY_LOOKUP
```

例：把参数换为catalog 神话 "" 3 0可浏览神话目录，再沿next_offset继续；换为analysis "" FWX-052 1 0可按别名查同父CH2-007。顺序只是稳定ID顺序，不是质量排名。查询只读本索引，不调用或修改query_knowledge.py。

## 证据边界

CH2-007的武侠依据是FWX-052新补证，不是旧BFI短评；CH2-004的东方玄幻与武侠标签具有不同窄范围。Frozen是第三方托管、封面9/23/13的Final Shooting Draft；Sony FINAL Conform是另一稿本身份；版本有限混合证据不统一改称成片实看。SCE-007的局部反击不代表核心已取回。

按同一来源合计精简，只留元数据、标准主题词、极短自有概括和问题；同文URL别名归一，不按卡重置范围。没有原文引文、歌词、完整剧本、原网页缓存、审核正文、私有项目或机器路径。来源公开和文件校验都不表示取得原文再分发权。使用这些资料不授权改稿、生图、发送或发布。

文件缺失或校验不符时只停用此可选入口，照常使用原Skill已具备的创作与检索能力。此索引自有校验，既有verify_knowledge.py通过不能代替这里的校验。
