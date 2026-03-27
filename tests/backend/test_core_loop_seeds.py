from app.core_loop.seeds import get_event_templates, get_realm_configs


def test_seed_contains_minimum_realms_and_events() -> None:
    realms = get_realm_configs()
    events = get_event_templates()

    assert len(realms) >= 4
    assert [realm.key for realm in realms[:4]] == [
        "qi_refining_early",
        "qi_refining_mid",
        "qi_refining_late",
        "qi_refining_peak",
    ]
    assert len(events) >= 5
