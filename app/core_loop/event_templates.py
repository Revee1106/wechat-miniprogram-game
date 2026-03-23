from __future__ import annotations

from app.core_loop.types import EventTemplateConfig


EVENT_TEMPLATE_CONFIGS: list[EventTemplateConfig] = [
    EventTemplateConfig(
        event_id="evt_cultivation_spirit_tide_001",
        event_name="Spirit Tide Meditation",
        event_type="cultivation",
        option_ids=[
            "opt_cultivation_spirit_tide_absorb",
            "opt_cultivation_spirit_tide_withdraw",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_mountain_breathing_002",
        event_name="Mountain Breathing",
        event_type="cultivation",
        option_ids=[
            "opt_mountain_breathing_meditate",
            "opt_mountain_breathing_forage",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_wandering_merchant_003",
        event_name="Wandering Merchant",
        event_type="encounter",
        option_ids=[
            "opt_wandering_merchant_trade",
            "opt_wandering_merchant_observe",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_cave_whispers_004",
        event_name="Cave Whispers",
        event_type="encounter",
        option_ids=[
            "opt_cave_whispers_explore",
            "opt_cave_whispers_withdraw",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_pill_oven_005",
        event_name="Pill Oven",
        event_type="crafting",
        option_ids=[
            "opt_pill_oven_refine",
            "opt_pill_oven_skip",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_dwelling_tax_006",
        event_name="Dwelling Tax",
        event_type="management",
        option_ids=[
            "opt_dwelling_tax_maintain",
            "opt_dwelling_tax_ignore",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_forest_gather_007",
        event_name="Forest Gather",
        event_type="resource",
        option_ids=[
            "opt_forest_gather_search",
            "opt_forest_gather_rest",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_lake_reflection_008",
        event_name="Lake Reflection",
        event_type="cultivation",
        option_ids=[
            "opt_lake_reflection_contemplate",
            "opt_lake_reflection_leave",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_bandit_ridge_009",
        event_name="Bandit Ridge",
        event_type="combat",
        option_ids=[
            "opt_bandit_ridge_ambush",
            "opt_bandit_ridge_evade",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_herb_market_010",
        event_name="Herb Market",
        event_type="trade",
        option_ids=[
            "opt_herb_market_buy",
            "opt_herb_market_haggle",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_pilgrim_shrine_011",
        event_name="Pilgrim Shrine",
        event_type="ritual",
        option_ids=[
            "opt_pilgrim_shrine_pray",
            "opt_pilgrim_shrine_offer",
        ],
    ),
    EventTemplateConfig(
        event_id="evt_ancient_scroll_012",
        event_name="Ancient Scroll",
        event_type="relic",
        option_ids=[
            "opt_ancient_scroll_read",
            "opt_ancient_scroll_seal",
        ],
    ),
]
