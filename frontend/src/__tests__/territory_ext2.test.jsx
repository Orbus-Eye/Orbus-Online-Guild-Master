/**
 * ROUND 11.2 EXT-2 — Frontend unit tests for Territory cost preview UI.
 *
 * 5 tests covering the two new components in isolation. The full E2E
 * "click Potenzia, get toast, re-fetch" loop is exercised by the
 * `e1_tester` browser harness (see Round 11.2 EXT-2 ticket).
 *
 * FE.01 — CostBreakdown renders gold owned/required with ✅ when sufficient.
 * FE.02 — CostBreakdown renders ❌ + missing summary when can_afford=false.
 * FE.03 — CostBreakdown.materials_detail row click fires onMaterialClick(slug).
 * FE.04 — MaterialSourceModal fetches lookup endpoint on open and renders
 *         display name + sources list.
 * FE.05 — MaterialSourceModal handles 404 → "Materiale non documentato".
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import CostBreakdown from "../components/territory/CostBreakdown";
import MaterialSourceModal from "../components/territory/MaterialSourceModal";

// Mock the api module BEFORE importing MaterialSourceModal would also work,
// but jest.mock is hoisted so we keep it together with the test bodies.
jest.mock("../lib/api", () => ({
    api: {
        get: jest.fn(),
    },
}));

// Resolve the mock after the module loads.
import { api as mockedApi } from "../lib/api";

beforeEach(() => {
    mockedApi.get.mockReset();
});

// ─── FE.01 ────────────────────────────────────────────────────────────────
test("FE.01 — CostBreakdown: gold sufficient renders ✅", () => {
    const cost = {
        target_level: 2,
        gold: 200,
        owned_gold: 500,
        can_afford: true,
        materials: {},
        materials_detail: [],
        missing: { gold: 0, materials: [] },
    };
    render(<CostBreakdown nextLevelCost={cost} lang="it" slug="guild_hall" />);
    const goldRow = screen.getByTestId("cost-row-gold-guild_hall");
    expect(goldRow).toHaveTextContent("Oro");
    expect(goldRow).toHaveTextContent("500/200");
    expect(goldRow.textContent).toMatch(/✅/);
    // No "missing" summary when can_afford === true.
    expect(screen.queryByTestId("cost-missing-summary-guild_hall")).toBeNull();
});

// ─── FE.02 ────────────────────────────────────────────────────────────────
test("FE.02 — CostBreakdown: can_afford=false shows ❌ and missing summary", () => {
    const cost = {
        target_level: 7,
        gold: 8500,
        owned_gold: 1000,
        can_afford: false,
        materials: { iron_shard: 24, greater_arcane_dust: 3 },
        materials_detail: [
            { slug: "iron_shard", display_name_it: "Frammento di Ferro", required: 24, owned: 5, missing: 19 },
            { slug: "greater_arcane_dust", display_name_it: "Polvere Arcana Maggiore", required: 3, owned: 0, missing: 3 },
        ],
        missing: {
            gold: 7500,
            materials: [
                { slug: "iron_shard", display_name_it: "Frammento di Ferro", missing: 19 },
                { slug: "greater_arcane_dust", display_name_it: "Polvere Arcana Maggiore", missing: 3 },
            ],
        },
    };
    render(<CostBreakdown nextLevelCost={cost} lang="it" slug="dormitories" />);
    const goldRow = screen.getByTestId("cost-row-gold-dormitories");
    expect(goldRow.textContent).toMatch(/❌/);
    const ironRow = screen.getByTestId("cost-row-mat-iron_shard-dormitories");
    expect(ironRow).toHaveTextContent("Frammento di Ferro");
    expect(ironRow).toHaveTextContent("5/24");
    const summary = screen.getByTestId("cost-missing-summary-dormitories");
    expect(summary).toHaveTextContent("7500g");
    expect(summary).toHaveTextContent("19× Frammento di Ferro");
});

// ─── FE.03 ────────────────────────────────────────────────────────────────
test("FE.03 — CostBreakdown: material row click → onMaterialClick(slug)", () => {
    const onClick = jest.fn();
    const cost = {
        target_level: 7,
        gold: 8500,
        owned_gold: 0,
        can_afford: false,
        materials_detail: [
            { slug: "iron_shard", display_name_it: "Frammento di Ferro", required: 24, owned: 0, missing: 24 },
        ],
        missing: { gold: 8500, materials: [] },
    };
    render(
        <CostBreakdown
            nextLevelCost={cost}
            lang="it"
            slug="dormitories"
            onMaterialClick={onClick}
        />,
    );
    const matRow = screen.getByTestId("cost-row-mat-iron_shard-dormitories");
    fireEvent.click(matRow);
    expect(onClick).toHaveBeenCalledWith("iron_shard");
});

// ─── FE.04 ────────────────────────────────────────────────────────────────
test("FE.04 — MaterialSourceModal: open → GET lookup + sources rendered", async () => {
    mockedApi.get.mockResolvedValueOnce({
        data: {
            slug: "iron_shard",
            display_name_it: "Frammento di Ferro",
            display_name_en: "Iron Shard",
            rarity: "common",
            description_it: "Scheggia di ferro grezzo.",
            description_en: "Crude iron shard.",
            sources: [
                { type: "dungeon", label_it: "Dungeon", label_en: "Dungeons", tier: "T1", note_it: "Lv1-3" },
                { type: "forge_disenchant", label_it: "Disincanto (Fucina)", label_en: "Forge disenchant" },
            ],
            used_for_it: ["Potenziamento Dormitori"],
        },
    });
    render(
        <MaterialSourceModal slug="iron_shard" open={true} onOpenChange={() => {}} lang="it" />,
    );
    await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith("/materials/lookup/iron_shard");
    });
    expect(await screen.findByTestId("material-source-modal")).toBeInTheDocument();
    expect(await screen.findByTestId("material-modal-title")).toHaveTextContent("Frammento di Ferro");
    expect(screen.getByTestId("material-modal-rarity")).toHaveTextContent("COMMON");
    expect(await screen.findByTestId("material-modal-source-dungeon")).toHaveTextContent("Dungeon");
    expect(screen.getByTestId("material-modal-source-forge_disenchant")).toHaveTextContent("Disincanto (Fucina)");
    expect(screen.getByTestId("material-modal-used-for")).toHaveTextContent("Potenziamento Dormitori");
});

// ─── FE.05 ────────────────────────────────────────────────────────────────
test("FE.05 — MaterialSourceModal: 404 → 'Materiale non documentato'", async () => {
    mockedApi.get.mockRejectedValueOnce({ response: { status: 404 } });
    render(
        <MaterialSourceModal slug="legendary_sword" open={true} onOpenChange={() => {}} lang="it" />,
    );
    await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith("/materials/lookup/legendary_sword");
    });
    expect(await screen.findByTestId("material-modal-description"))
        .toHaveTextContent(/Materiale non documentato/);
    // Equipment slugs MUST NOT render a sources list.
    expect(screen.queryByTestId("material-modal-sources")).toBeNull();
});
