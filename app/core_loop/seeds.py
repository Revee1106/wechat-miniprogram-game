from __future__ import annotations

from app.core_loop.types import EventChoice, EventTemplate, RealmConfig


def get_realm_configs() -> list[RealmConfig]:
    return [
        RealmConfig("qi_refining", "炼气", 6, 0.85, 100),
        RealmConfig("foundation", "筑基", 12, 0.65, 240),
        RealmConfig("golden_core", "金丹", 24, 0.45, 480),
        RealmConfig("nascent_soul", "元婴", 40, 0.30, 960),
    ]


def get_event_templates() -> list[EventTemplate]:
    return [
        EventTemplate(
            key="mountain_breathing",
            display_name="山门吐纳",
            description="晨雾未散，你可以静修吐纳，也可以顺手采些山草。",
            realm_keys=["qi_refining", "foundation", "golden_core", "nascent_soul"],
            weight=10,
            region="starter-valley",
            choices=[
                EventChoice(
                    key="meditate",
                    display_name="静坐吐纳",
                    description="稳扎稳打地积累修为。",
                    cultivation_exp_delta=18,
                    spirit_stone_delta=2,
                ),
                EventChoice(
                    key="forage",
                    display_name="采集草药",
                    description="换取一些日常修炼资源。",
                    spirit_stone_delta=6,
                ),
            ],
        ),
        EventTemplate(
            key="wandering_merchant",
            display_name="游商过境",
            description="一位游商愿意用灵石换取你手里的草药。",
            realm_keys=["qi_refining", "foundation"],
            weight=6,
            region="starter-valley",
            choices=[
                EventChoice(
                    key="trade",
                    display_name="售卖草药",
                    description="把草药换成更通用的灵石。",
                    spirit_stone_delta=10,
                ),
                EventChoice(
                    key="observe",
                    display_name="旁观行情",
                    description="记住价格波动，增长一点见识。",
                    cultivation_exp_delta=8,
                ),
            ],
        ),
        EventTemplate(
            key="cave_whispers",
            display_name="洞窟低语",
            description="洞窟深处似乎藏着机缘，也可能暗伏杀机。",
            realm_keys=["foundation", "golden_core", "nascent_soul"],
            weight=5,
            region="fog-cave",
            choices=[
                EventChoice(
                    key="explore",
                    display_name="深入洞窟",
                    description="搏一把机缘。",
                    cultivation_exp_delta=30,
                    spirit_stone_delta=12,
                    death_chance=1.0,
                ),
                EventChoice(
                    key="withdraw",
                    display_name="谨慎退避",
                    description="保全性命，少得一点资源。",
                    spirit_stone_delta=3,
                ),
            ],
        ),
        EventTemplate(
            key="pill_oven",
            display_name="丹炉余火",
            description="残留的丹火还热着，正适合小试炼药。",
            realm_keys=["qi_refining", "foundation", "golden_core"],
            weight=4,
            region="starter-valley",
            choices=[
                EventChoice(
                    key="refine",
                    display_name="顺手炼丹",
                    description="消耗寿元，换取突破助力。",
                    cultivation_exp_delta=10,
                    lifespan_delta=-1,
                ),
                EventChoice(
                    key="skip",
                    display_name="暂不尝试",
                    description="维持当前节奏继续修行。",
                    spirit_stone_delta=1,
                ),
            ],
        ),
        EventTemplate(
            key="dwelling_tax",
            display_name="洞府 upkeep",
            description="洞府需要灵石维护，但也能反哺修炼。",
            realm_keys=["qi_refining", "foundation", "golden_core", "nascent_soul"],
            weight=3,
            region="starter-valley",
            choices=[
                EventChoice(
                    key="maintain",
                    display_name="维护洞府",
                    description="投入一点灵石，换取稳定状态。",
                    spirit_stone_delta=-3,
                    cultivation_exp_delta=12,
                ),
                EventChoice(
                    key="ignore",
                    display_name="暂时搁置",
                    description="省下资源，但效率下降。",
                    lifespan_delta=-1,
                ),
            ],
        ),
    ]
