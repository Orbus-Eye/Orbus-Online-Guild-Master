// FASE 10A — P0: un nuovo avventuriero classless deve poter APRIRE la
// scelta classe senza schermata di errore.
//
// Root cause del bug tester: il backend (FASE 9) serve class_mechanic
// SENZA `builds`, ma la griglia delle 27 Sale faceva
// `hall.class_mechanic.builds.map(...)` → TypeError in render → crash
// dell'intera pagina Sale di Classe appena esisteva una recluta senza
// classe. Questo test monta il journey con il payload REALE del backend
// post-FASE 9 e fallisce se il render esplode di nuovo.
import { MemoryRouter } from "react-router-dom";
import { render, screen, waitFor } from "@testing-library/react";

import ClassHallAssignmentJourney from "../components/ClassHallAssignmentJourney";
import { api } from "../lib/api";

jest.mock("../lib/api", () => ({
    api: { get: jest.fn(), post: jest.fn() },
    formatApiError: (e) => String(e?.message || e),
}));

// Payload identico alla shape attuale di /class-halls/assignment/choices
// (class_mechanic_public: niente builds, solo resonance/counter tags).
const hall = (overrides = {}) => ({
    hall_id: "hall_guerriero",
    canonical_class_slug: "guerriero",
    class_name_it: "Guerriero",
    class_proficiency: "guerriero",
    class_role: "DPS",
    hall_name_it: "Sala della Lama Rovente",
    primary_stat: "strength",
    armor_tags: ["plate"],
    weapon_tags: ["sword"],
    hall_master_witness_npc: "Maestra Ilva",
    lore_hook_it: "Il ferro ricorda ogni giuramento.",
    gameplay_style_it: "Mischia diretta.",
    starter_item_name_it: "Lama del Giuramento",
    trial_steps: ["saluta_il_maestro", "prova_di_forza"],
    wave: "A",
    assignment_enabled: true,
    assignment_requires_trial: true,
    assignment_requires_confirmation: true,
    trial_reward_enabled: false,
    class_mechanic: {
        mechanic_id: "furia_del_guerriero",
        name_it: "Furia del Guerriero",
        summary_it: "Colpi più pesanti quando l'equip risuona.",
        primary_stat: "strength",
        counter_tags: ["armored"],
        resonance_tags: ["plate", "sword"],
        // NIENTE `builds`: eliminate in FASE 9.
    },
    ...overrides,
});

const classlessRecruit = {
    id: "adv-new-1",
    name: "Recluta Nuova",
    level: 1,
    class_selection_required: true,
};

function mockBackend({ halls, adventurers }) {
    api.get.mockImplementation((url) => {
        if (url === "/class-halls/assignment/choices") {
            return Promise.resolve({ data: { halls } });
        }
        if (url === "/adventurers") {
            return Promise.resolve({ data: { adventurers } });
        }
        return Promise.reject(new Error(`unexpected GET ${url}`));
    });
}

const renderJourney = () => render(
    <MemoryRouter>
        <ClassHallAssignmentJourney />
    </MemoryRouter>,
);

describe("ClassHallAssignmentJourney — P0 scelta classe nuovo avventuriero", () => {
    beforeEach(() => jest.clearAllMocks());

    it("apre la griglia Sale con una recluta classless SENZA crashare", async () => {
        mockBackend({
            halls: [
                hall(),
                hall({
                    hall_id: "hall_paladino",
                    canonical_class_slug: "paladino",
                    class_name_it: "Paladino",
                    class_role: "TANK",
                    class_mechanic: {
                        mechanic_id: "egida_sacra",
                        name_it: "Egida Sacra",
                        summary_it: "Protegge il gruppo.",
                        primary_stat: "endurance",
                        counter_tags: ["undead"],
                        resonance_tags: ["shield", "plate"],
                    },
                }),
            ],
            adventurers: [classlessRecruit],
        });

        renderJourney();

        await waitFor(() => {
            expect(
                screen.getByTestId("class-hall-assignment-journey"),
            ).toBeInTheDocument();
        });
        // La recluta è selezionabile e le Sale sono visibili.
        expect(screen.getByText("Recluta Nuova")).toBeInTheDocument();
        expect(screen.getByText("Guerriero")).toBeInTheDocument();
        expect(screen.getByText("Paladino")).toBeInTheDocument();
        // I tag di risonanza sostituiscono le vecchie build.
        expect(screen.getByTestId("hall-mechanic-hall_guerriero"))
            .toHaveTextContent("Furia del Guerriero");
        expect(screen.getByTestId("hall-mechanic-hall_guerriero"))
            .toHaveTextContent("plate");
    });

    it("regge anche class_mechanic null o senza resonance_tags", async () => {
        mockBackend({
            halls: [
                hall({ class_mechanic: null }),
                hall({
                    hall_id: "hall_alchimista",
                    class_name_it: "Alchimista",
                    class_mechanic: {
                        mechanic_id: "trasmutazione",
                        name_it: "Trasmutazione",
                        summary_it: "Distilla il potere.",
                        primary_stat: "intellect",
                        counter_tags: [],
                        // resonance_tags assente: non deve crashare.
                    },
                }),
            ],
            adventurers: [classlessRecruit],
        });

        renderJourney();

        await waitFor(() => {
            expect(screen.getByText("Alchimista")).toBeInTheDocument();
        });
    });

    it("senza reclute classless mostra il rimando al reclutamento", async () => {
        mockBackend({
            halls: [hall()],
            adventurers: [
                { id: "adv-old", name: "Veterano", level: 12, class_selection_required: false },
            ],
        });

        renderJourney();

        await waitFor(() => {
            expect(screen.getByText("Vai al reclutamento")).toBeInTheDocument();
        });
    });
});
