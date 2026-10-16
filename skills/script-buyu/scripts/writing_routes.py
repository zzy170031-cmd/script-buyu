"""Explainable phrase routes to reading passages; never a quality or read receipt."""
import re
import unicodedata


def normalized(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value).casefold())


# Separate from golden/method records: these are navigation, not new evidence cards.
ROUTES = (
    ('stiff_dialogue', ('对白生硬', '台词生硬', '说话别扭', '对白不自然', '台词不自然', '书面腔', '语体跳变'),
     ('references/dialogue-craft.md#先找到这部故事的说话方式',
      'references/dialogue-craft.md#词语句式与语体的取舍'),
     '按本篇关系、处境和语言幅度判断，不靠统一短句或填语气词。',
     ('references/writing-choice-cases.md#长解释和没接住话各在写什么',)),
    ('exposition', ('解释腔', '说明腔', '像说明书', '像百科', '说教味', '对白解释过多', '设定搬运'),
     ('references/dialogue-craft.md#把材料写成有分量的场面',
      'references/text-review.md#按症状选择修订尺度'),
     '比较说明在当前交流中的用途与删移损失；必要解释、直答和试探可以保留。',
     ('references/writing-choice-cases.md#长解释和没接住话各在写什么',)),
    ('speaker_clarity', ('说话人不清', '说话人分不清', '谁在说话', '对白归属不清', '指代不清'),
     ('references/dialogue-craft.md#先找到这部故事的说话方式',
      'references/dialogue-craft.md#从发言到接收先辨清当前对象'),
     '先查主体、听者及切换锚点；清楚问答不逐句添姓名。只有叙述/转述层次混淆才需比较Piazza，普通归属可只用章节。',
     ('references/writing-choice-cases.md#展开概述和评论由谁承担',)),
    ('same_voice', ('人物口吻雷同', '口吻雷同', '声音雷同', '一个腔', '人物说话一样', '说话一个味'),
     ('references/dialogue-craft.md#先找到这部故事的说话方式',
      'references/dialogue-craft.md#词语句式与语体的取舍'),
     '比较人物当下所求、用词及句式；共同术语或短命令相似并不自动有错。',
     ('references/writing-choice-cases.md#长解释和没接住话各在写什么',)),
)

NOTICE = ('Phrase-matched navigation only, not semantic diagnosis, index matches or proof of reading. '
          'Read the relevant context and limits before use; do not load every suggestion or expand revision authority. '
          'The three contextual studies are inherited text analyses, not new original-work reading or quality validation.')


def resource_routes(query):
    text = normalized(query)
    found = []
    for problem, aliases, sections, reason, cases in ROUTES:
        matched = [alias for alias in aliases if normalized(alias) in text]
        if not matched:
            continue
        found.append({'problem': problem, 'matched_phrases': matched,
                      'chapters': list(sections), 'why': reason,
                      'contextual_cases': list(cases), 'notice': NOTICE})
    # This bridge is conditional: the film record is only about professional direction.
    if found and '合作' in text and any(word in text for word in ('职业', '去留', '重复劳动')):
        found[0]['optional_scene_study'] = {
            'guide': 'references/scene-study-library.md#查读',
            'index': 'data/scene-study-index.json', 'section': 'curated_analysis',
            'case_id': 'MB001',
            'why': '仅在当前交流涉及职业改向/合作去留时比较；不是一般口吻模板。',
            'limits': '继承Taubin评论L39–43的窄文字分析；未实看或听音，不扩展标签、事实或质量结论。'}
    return found
