from app.scripts.t6_item_pool_simulation import build_simulation_report


def test_t6_pool_simulation_passes_without_endgame_leaks():
    report = build_simulation_report(iterations=20_000)
    assert report["valid"], report["errors"]
    assert report["catalog"]["total"] == 1500
    assert report["company_ring"]["included_in_dungeon_or_raid_pool"] is False
    assert (
        report["company_ring"]["expected_grants_per_million_eligible_rolls"]
        == 1
    )
    for outcomes in report["dungeons"].values():
        for branch in outcomes.values():
            assert not (
                set(branch["rarity_counts"]) & {"Legendary", "Unique"}
            )
    for outcomes in report["raids"].values():
        for branch in outcomes.values():
            assert "Unique" not in branch["rarity_counts"]
