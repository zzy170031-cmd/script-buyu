"""Original miniature fiction for software tests, unrelated to user material."""


def story():
    return {
        "schema_version": "1.0", "revision": 1, "status": "awaiting_user_confirmation",
        "project": {"project_id": "TEST-LIGHT", "title": "远灯驿站", "genre": "科幻群像", "domain": "原创虚构空间站", "audience": "成年观众", "medium": "2D动画", "viewpoint": "第三人称", "episode_count": 2, "target_duration_seconds": 120},
        "logline": "两名守站员为了救下一艘失联渡船，必须在求救灯和保温设备之间重新分配电力。",
        "synopsis": "阿砚坚持亮灯，陆禾担心住客失温，两人各自占据配电台一侧。\n当他们发现渡船正沿旧标记航行，陆禾交出备用电池，阿砚也放弃整夜常亮的计划，改用约定的短闪引路。",
        "characters": [
            {"character_id": "C1", "name": "阿砚", "description": "年轻守站员，知道旧航线，却总想独自承担风险。", "arc": "从抢占配电权限，到愿意说明信息并接受协作。"},
            {"character_id": "C2", "name": "陆禾", "description": "值班维修员，守着住客的保温承诺。", "arc": "从封闭配电柜，到用可承受的代价共同救援。"}],
        "world_rules": ["备用电池只能承担一种持续负载，间歇发光可以降低耗电。"],
        "episodes": [{"episode_id": "EP1", "title": "灯灭以前", "target_duration_seconds": 60}, {"episode_id": "EP2", "title": "短闪", "target_duration_seconds": 60}],
        "scenes": [
            {"scene_id": "S1", "episode_id": "EP1", "heading": "内景 配电间 夜", "location": "驿站配电间", "time_weather": "风暴夜", "purpose": "让双方发现对方必须守住的东西。", "beats": [
                {"beat_id": "B1", "kind": "action", "speaker_id": None, "text": "阿砚把手按向灯闸。陆禾握住他的手腕，指向保温表上不断下降的数值。"},
                {"beat_id": "B2", "kind": "dialogue", "speaker_id": "C1", "text": "船上还有人。我见过他们走的那条旧线。"},
                {"beat_id": "B3", "kind": "dialogue", "speaker_id": "C2", "text": "这里也有人。告诉我，他们能看见什么信号？"},
                {"beat_id": "B4", "kind": "action", "speaker_id": None, "text": "阿砚松开灯闸，从衣袋取出旧航线图，把被折起的信号表摊给她。"}]},
            {"scene_id": "S2", "episode_id": "EP2", "heading": "内景 灯塔值班室 夜", "location": "驿站灯塔", "time_weather": "同夜 风暴减弱", "purpose": "让双方以共同承担的方案完成救援。", "beats": [
                {"beat_id": "B5", "kind": "action", "speaker_id": None, "text": "陆禾接上备用电池，把计时器递给阿砚。暖气仍在低声运转。"},
                {"beat_id": "B6", "kind": "dialogue", "speaker_id": "C2", "text": "每次三秒。你数，我守电表。"},
                {"beat_id": "B7", "kind": "action", "speaker_id": None, "text": "阿砚按约定短闪灯光。风雪深处回应两下微光；他停手等到电表回升，才继续下一组。"},
                {"beat_id": "B8", "kind": "dialogue", "speaker_id": "C1", "text": "看见了。下一组听你的。"},
                {"beat_id": "B9", "kind": "action", "speaker_id": None, "text": "渡船抵住码头。陆禾打开保温间，阿砚接过冻僵旅客的行李。两人腾出灯下的位置，让旅客先坐。"}]}]}
