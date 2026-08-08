// FASE 1 (2026-08-08) — Regressione "Deposito schermata nera".
//
// Bug: Inventory.jsx referenziava una variabile `slot` rimossa dal refactor
// R18.4 (sostituita da rawSlot/physicalSlots). Con almeno un oggetto in
// inventario il render lanciava `ReferenceError: slot is not defined` e,
// in assenza di ErrorBoundary, la pagina restava nera.
//
// Questo test monta la pagina con API mockate e verifica che:
//   1. la lista renderizza senza crash con item multi-slot (ring) e material;
//   2. il badge "equipaggiato da" copre anche gli slot ring_1/ring_2
//      (buildEquippedByMap scansiona tutti i 10 slot, non solo 3);
//   3. i materiali NON espongono azioni di equipaggiamento.
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Inventory from "../pages/Inventory";
import { I18nProvider } from "../i18n/I18nContext";

jest.mock("../lib/api", () => ({
    api: { get: jest.fn(), post: jest.fn() },
    formatApiError: (e) => String((e && e.message) || e),
}));

// AppHeader tira dentro auth/nav: fuori scope per questo test.
jest.mock("../components/AppHeader", () => ({
    __esModule: true,
    default: () => <div data-testid="app-header-stub" />,
}));

const { api } = require("../lib/api");

const RING_ITEM = {
    id: "item-ring",
    slug: "anello_di_prova",
    name: "Anello di Prova",
    display_name_it: "Anello di Prova",
    display_name_en: "Test Ring",
    item_type: "ring",
    slot_type: "ring",
    rarity: "Rare",
    power_score: 5,
    level_required: 1,
    agility_bonus: 2,
};

const MATERIAL_ITEM = {
    id: "item-mat",
    slug: "iron_shard",
    name: "Scheggia di Ferro",
    display_name_it: "Scheggia di Ferro",
    display_name_en: "Iron Shard",
    item_type: "material",
    rarity: "Common",
    power_score: 0,
};

function emptyEquipment() {
    return {
        weapon: null, chest: null, legs: null, head: null, accessory: null,
        back: null, ring_1: null, ring_2: null, trinket_1: null, trinket_2: null,
    };
}

const ADVENTURER = {
    id: "adv1",
    name: "Lyra Stoneheart",
    level: 12,
    is_available: true,
    class_role: "DPS",
    class_name: "Ladro",
    total_power: 100,
    equipment: {
        ...emptyEquipment(),
        // Anello indossato in ring_1 → il Deposito deve mostrarlo
        // come "equipaggiato da Lyra" (slot non-legacy).
        ring_1: { equipped_item_id: "eq1", slot: "ring_1", item: RING_ITEM },
    },
};

const INVENTORY_ROWS = [
    {
        id: "row-ring",
        guild_id: "g1",
        item_id: "item-ring",
        total_quantity: 2,
        equipped_quantity: 1,
        available_quantity: 1,
        refinement_level: 0,
        is_bound: false,
        bound_to_adventurer_id: null,
        item: RING_ITEM,
    },
    {
        id: "row-mat",
        guild_id: "g1",
        item_id: "item-mat",
        total_quantity: 10,
        equipped_quantity: 0,
        available_quantity: 10,
        refinement_level: 0,
        is_bound: false,
        bound_to_adventurer_id: null,
        item: MATERIAL_ITEM,
    },
];

beforeEach(() => {
    api.get.mockImplementation((url) => {
        if (url === "/inventory") {
            return Promise.resolve({ data: { inventory: INVENTORY_ROWS } });
        }
        if (url === "/adventurers") {
            return Promise.resolve({ data: { adventurers: [ADVENTURER] } });
        }
        if (url.startsWith("/recipes")) {
            return Promise.resolve({ data: { recipes: [] } });
        }
        return Promise.reject(new Error(`unexpected GET ${url}`));
    });
});

function renderPage() {
    return render(
        <I18nProvider>
            <MemoryRouter>
                <Inventory />
            </MemoryRouter>
        </I18nProvider>
    );
}

test("il Deposito renderizza le card senza crash (regressione schermata nera)", async () => {
    renderPage();
    // Se il render lancia (ReferenceError storico), findByTestId fallisce.
    await screen.findByTestId("inventory-cards");
    expect(screen.getByTestId("inventory-card-row-ring")).toBeInTheDocument();
    expect(screen.getByTestId("inventory-card-row-mat")).toBeInTheDocument();
    expect(screen.getByTestId("inventory-stack-count")).toHaveTextContent("2");
});

test("gli oggetti negli slot non-legacy (ring) risultano equipaggiati", async () => {
    renderPage();
    await screen.findByTestId("inventory-cards");
    const badge = screen.getByTestId("inv-status-equipped-row-ring");
    expect(badge).toHaveTextContent("Lyra Stoneheart");
});

test("i materiali non espongono azioni di equipaggiamento", async () => {
    renderPage();
    await screen.findByTestId("inventory-cards");
    // CTA modal + bottoni rapidi presenti per l'anello…
    expect(
        screen.getByTestId("inv-open-equip-modal-row-ring")
    ).toBeInTheDocument();
    // …ma MAI per un materiale (prima del fix compariva e falliva con 400).
    expect(
        screen.queryByTestId("inv-open-equip-modal-row-mat")
    ).not.toBeInTheDocument();
    expect(
        screen.queryByTestId("inv-no-eligible-row-mat")
    ).not.toBeInTheDocument();
});

test("il modal di equip segnala in anticipo chi indossa già l'oggetto", async () => {
    renderPage();
    await screen.findByTestId("inventory-cards");
    fireEvent.click(screen.getByTestId("inv-open-equip-modal-row-ring"));
    const notice = await screen.findByTestId("equip-modal-already-equipped");
    expect(notice).toHaveTextContent("Lyra Stoneheart");
});
