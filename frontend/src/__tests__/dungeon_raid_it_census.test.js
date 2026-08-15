// FASE 10B — censimento automatico anti-regressione: nessun testo
// player-facing INGLESE nei flussi Dungeon/Raid del frontend.
//
// 1. Scansione statica dei sorgenti: vieta i toast/popup EN già visti
//    dai tester (e i pattern affini) fuori dal sistema i18n.
// 2. Copertura i18n: ogni raid del catalogo server deve avere la voce
//    raids.catalog.<slug> in italiano (fallback quando un doc legacy
//    non porta ancora raid_name_it).
const fs = require("fs");
const path = require("path");

// Jest gira con cwd = frontend/: i sorgenti sono in ./src.
const SRC = path.resolve("src");

function collectSourceFiles(dir) {
    const out = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            if (entry.name === "__tests__" || entry.name === "node_modules") continue;
            out.push(...collectSourceFiles(full));
        } else if (/\.(jsx?|tsx?)$/.test(entry.name)) {
            out.push(full);
        }
    }
    return out;
}

// Frasi EN player-facing vietate nei sorgenti (toast/popup dungeon-raid).
const FORBIDDEN_LITERALS = [
    "Replay started",
    "Raid completed",
    "Dungeon completed",
    "Raid started",
    "Expedition completed",
    "Expedition failed",
    "Dungeon cleared",
];

// I 9 raid del catalogo server (round5 + R113).
const RAID_SLUGS = [
    "moonfall-vigil",
    "broken-bastion-siege",
    "necropolis-bells",
    "dragon-vault",
    "rituale-del-vuoto-orde",
    "figli-di-irthe-rising",
    "alevora-marionetta-grande",
    "tempio-del-vuoto-eterno",
    "valys-mordivac-final-whisper",
];

describe("censimento IT dungeon/raid", () => {
    it("nessun toast/popup EN vietato nei sorgenti", () => {
        const offenders = [];
        for (const file of collectSourceFiles(SRC)) {
            const text = fs.readFileSync(file, "utf8");
            for (const literal of FORBIDDEN_LITERALS) {
                if (text.includes(`"${literal}`) || text.includes(`\`${literal}`)
                    || text.includes(`'${literal}`)) {
                    offenders.push(`${path.relative(SRC, file)}: "${literal}"`);
                }
            }
        }
        expect(offenders).toEqual([]);
    });

    it("raids.catalog IT copre tutti i raid del server", () => {
        const it = JSON.parse(fs.readFileSync(
            path.join(SRC, "i18n", "lang", "it.json"), "utf8",
        ));
        const catalog = (it.raids && it.raids.catalog) || {};
        const missing = RAID_SLUGS.filter((slug) => !catalog[slug]?.name);
        expect(missing).toEqual([]);
        // E i nomi sono davvero italiani, non copie EN note.
        expect(catalog["moonfall-vigil"].name).toBe("Veglia della Luna Infranta");
        expect(catalog["necropolis-bells"].name).toMatch(/Campane|Irthe/);
    });

    it("le spedizioni preferiscono il nome IT server-authoritative", () => {
        // Il helper condiviso è l'unico punto di rendering dei nomi
        // dungeon nelle liste/report: deve preferire dungeon_name_it.
        jest.isolateModules(() => {
            const { expeditionDungeonName } = require("../i18n/contentMap");
            const tContent = (group, slug, field, fallback) => fallback;
            expect(expeditionDungeonName(tContent, {
                dungeon_name: "Goblin Warrens",
                dungeon_name_it: "Tane dei Goblin",
            }, "it")).toBe("Tane dei Goblin");
            // Doc legacy senza campo IT: reverse-map o fallback EN.
            expect(expeditionDungeonName(tContent, {
                dungeon_name: "Nome Sconosciuto",
            }, "it")).toBe("Nome Sconosciuto");
        });
    });
});
