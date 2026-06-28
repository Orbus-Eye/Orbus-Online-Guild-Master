// ROUND 6A.2a — Squad builder (new + edit, shared component).
// Uniform UX across dungeon_3 / dungeon_5 / raid_20. For raid_20 the pool
// stays at the top and the 4 party slots render in a 2×2 grid below.
import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import AppHeader from "@/components/AppHeader";
import { useT } from "@/i18n/I18nContext";
// ROUND 6B.3 Wave 3 — FIX BUG 2: normalise structured backend `detail`
// payloads to a safe string before passing to `toast.error`.
import { formatErrorDetail } from "@/lib/api";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPE_META = {
    dungeon_3: { size: 3, titleIt: "Dungeon 3", titleEn: "Dungeon 3", isRaid: false },
    dungeon_5: { size: 5, titleIt: "Dungeon 5", titleEn: "Dungeon 5", isRaid: false },
    raid_20: { size: 20, titleIt: "Raid 20", titleEn: "Raid 20", isRaid: true },
};

const ROLE_MARKER = { Tank: "[T]", Healer: "[H]", DPS: "[D]", Support: "[S]" };

function fetchJSON(url, init = {}) {
    const token = localStorage.getItem("orbus_token");
    return fetch(url, {
        ...init,
        headers: { ...(init.headers || {}), Authorization: `Bearer ${token}` },
    });
}

function AdvChip({ adv, onClick, disabled, action, testid }) {
    const marker = ROLE_MARKER[adv.class_role] || "[?]";
    return (
        <button
            type="button"
            disabled={disabled}
            onClick={onClick}
            data-testid={testid}
            className={`text-left p-2 border rounded-sm transition-colors text-[11px] tracking-wide ${
                disabled
                    ? "border-neutral-800 bg-neutral-900/40 text-muted-foreground opacity-40 cursor-not-allowed"
                    : "border-neutral-700 hover:border-amber/60 hover:bg-secondary/60 text-foreground"
            }`}
        >
            <div className="flex justify-between items-baseline">
                <span className="font-bold">
                    <span className="text-amber">{marker}</span> {adv.name}
                </span>
                <span className="text-amber font-bold">PWR {adv.total_power ?? adv.base_power ?? 0}</span>
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">
                {adv.class_name} · {adv.rarity} · L{adv.level}
            </div>
            {action && <div className="text-[10px] text-amber/80 mt-1">{action}</div>}
        </button>
    );
}

function composeWarnings(advs, lang) {
    const warnings = [];
    const roles = advs.map((a) => a?.class_role).filter(Boolean);
    if (advs.length > 0) {
        if (!roles.includes("Tank")) warnings.push(lang === "it" ? "Manca Tank" : "Missing Tank");
        if (!roles.includes("Healer")) warnings.push(lang === "it" ? "Manca Healer" : "Missing Healer");
        const dps = roles.filter((r) => r === "DPS").length;
        if (advs.length >= 5 && dps >= 4) warnings.push(lang === "it" ? "Troppi DPS" : "Too many DPS");
    }
    return warnings;
}

export default function SquadBuilder() {
    const { lang } = useT();
    const navigate = useNavigate();
    const { id } = useParams();
    const [searchParams] = useSearchParams();
    const isEdit = !!id;

    const [squadType, setSquadType] = useState(searchParams.get("type") || "dungeon_3");
    const [name, setName] = useState("");
    const [pool, setPool] = useState([]);  // all guild adventurers
    const [selected, setSelected] = useState([]);  // adventurer_ids in main list
    const [parties, setParties] = useState({ party_1: [], party_2: [], party_3: [], party_4: [] });
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const meta = TYPE_META[squadType];

    const advById = useMemo(() => {
        const idx = {};
        for (const a of pool) idx[a.id] = a;
        return idx;
    }, [pool]);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const advRes = await fetchJSON(`${API}/adventurers`);
            if (advRes.status === 401) {
                navigate("/login");
                return;
            }
            const advBody = await advRes.json();
            setPool(advBody.adventurers || []);

            if (isEdit) {
                const sRes = await fetchJSON(`${API}/squads/${id}`);
                if (!sRes.ok) {
                    toast.error(lang === "it" ? "Squadra non trovata" : "Squad not found");
                    navigate("/squads");
                    return;
                }
                const sBody = await sRes.json();
                setSquadType(sBody.squad_type);
                setName(sBody.name);
                setSelected(sBody.adventurer_ids || []);
                if (sBody.squad_type === "raid_20" && sBody.raid_parties) {
                    setParties(sBody.raid_parties);
                }
            } else {
                // ROUND 6B.2c — "Save as squad" deep-link from victory reports.
                // Accepts ?adventurer_ids=id1,id2,... and optional ?suggested_name=Foo
                const idsParam = searchParams.get("adventurer_ids");
                if (idsParam) {
                    const ids = idsParam.split(",").filter(Boolean).slice(0, 20);
                    setSelected(ids);
                    // For raid_20, distribute flat 5+5+5+5 if exactly 20 ids
                    const t = searchParams.get("type") || "dungeon_3";
                    if (t === "raid_20" && ids.length === 20) {
                        setParties({
                            party_1: ids.slice(0, 5),
                            party_2: ids.slice(5, 10),
                            party_3: ids.slice(10, 15),
                            party_4: ids.slice(15, 20),
                        });
                    }
                }
                const sugg = searchParams.get("suggested_name");
                if (sugg) setName(sugg.slice(0, 40));
            }
        } finally {
            setLoading(false);
        }
    }, [id, isEdit, lang, navigate, searchParams]);

    useEffect(() => {
        load();
    }, [load]);

    const filteredPool = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (!q) return pool;
        return pool.filter(
            (a) =>
                (a.name || "").toLowerCase().includes(q) ||
                (a.class_name || "").toLowerCase().includes(q) ||
                (a.class_role || "").toLowerCase().includes(q) ||
                (a.rarity || "").toLowerCase().includes(q),
        );
    }, [pool, search]);

    const isRaid = meta.isRaid;

    // ─── helpers ──────────────────────────────────────────────────────────
    const allInParties = isRaid
        ? [...parties.party_1, ...parties.party_2, ...parties.party_3, ...parties.party_4]
        : [];
    const isAssigned = (advId) =>
        isRaid ? allInParties.includes(advId) : selected.includes(advId);
    const filledCount = isRaid ? allInParties.length : selected.length;
    const totalPower = (isRaid ? allInParties : selected)
        .map((aid) => advById[aid])
        .filter(Boolean)
        .reduce((acc, a) => acc + (a.total_power ?? a.base_power ?? 0), 0);
    const warnings = composeWarnings(
        (isRaid ? allInParties : selected).map((aid) => advById[aid]).filter(Boolean),
        lang,
    );

    const toggleDungeon = (advId) => {
        setSelected((prev) =>
            prev.includes(advId)
                ? prev.filter((x) => x !== advId)
                : prev.length >= meta.size
                  ? prev
                  : [...prev, advId],
        );
    };

    const addToParty = (partyKey, advId) => {
        setParties((prev) => {
            if (prev[partyKey].includes(advId)) return prev;
            if (allInParties.includes(advId)) return prev;
            if (prev[partyKey].length >= 5) {
                toast.error(lang === "it" ? "Party piena (5/5)" : "Party full (5/5)");
                return prev;
            }
            return { ...prev, [partyKey]: [...prev[partyKey], advId] };
        });
    };

    const removeFromParty = (partyKey, advId) => {
        setParties((prev) => ({ ...prev, [partyKey]: prev[partyKey].filter((x) => x !== advId) }));
    };

    const [activeParty, setActiveParty] = useState("party_1");

    // ROUND 6A.2a — derived `canSave` so the Save button mirrors backend
    // validation exactly. Avoids the confusing 422 round-trip the tester
    // flagged on partial raid_20 fills.
    const nameOk = name.trim().length >= 2;
    const sizeOk = filledCount === meta.size;
    const partyOk = !isRaid || ["party_1", "party_2", "party_3", "party_4"].every(
        (p) => parties[p].length === 5,
    );
    const canSave = nameOk && sizeOk && partyOk;
    // Reason hint shown as `title` tooltip on the disabled button.
    let saveDisabledReason = "";
    if (!nameOk) {
        saveDisabledReason = lang === "it"
            ? "Nome richiesto (min 2 caratteri)"
            : "Name required (min 2 chars)";
    } else if (!sizeOk) {
        const missing = meta.size - filledCount;
        saveDisabledReason = lang === "it"
            ? `Mancano ${missing} avventurieri`
            : `Missing ${missing} adventurers`;
    } else if (!partyOk) {
        const wrong = ["party_1", "party_2", "party_3", "party_4"]
            .map((p, i) => ({ p, i, n: parties[p].length }))
            .filter((x) => x.n !== 5);
        const detail = wrong.map((x) => `P${x.i + 1}: ${x.n}/5`).join(", ");
        saveDisabledReason = lang === "it"
            ? `Party incomplete (${detail})`
            : `Incomplete parties (${detail})`;
    }

    const save = async () => {
        if (!name.trim()) {
            toast.error(lang === "it" ? "Nome obbligatorio" : "Name required");
            return;
        }
        const expected = meta.size;
        if (filledCount !== expected) {
            toast.error(
                lang === "it"
                    ? `Servono ${expected} membri (hai ${filledCount})`
                    : `Need ${expected} members (you have ${filledCount})`,
            );
            return;
        }
        const adventurer_ids = isRaid ? allInParties : selected;
        const payload = { name: name.trim(), squad_type: squadType, adventurer_ids };
        if (isRaid) payload.raid_parties = parties;

        setSaving(true);
        try {
            const url = isEdit ? `${API}/squads/${id}` : `${API}/squads`;
            const method = isEdit ? "PATCH" : "POST";
            // For PATCH we keep name + adventurer_ids + raid_parties
            const res = await fetchJSON(url, {
                method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const body = await res.json();
            if (!res.ok) {
                toast.error(formatErrorDetail(body.detail) || (lang === "it" ? "Errore" : "Error"));
                return;
            }
            toast.success(lang === "it" ? "Squadra salvata" : "Squad saved");
            navigate("/squads");
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <AppHeader />
                <main className="max-w-6xl mx-auto px-4 py-8" data-testid="squad-builder-loading">
                    {lang === "it" ? "Caricamento..." : "Loading..."}
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-6xl mx-auto px-4 py-6" data-testid="squad-builder-page">
                {/* Header */}
                <div className="mb-5 flex items-end justify-between gap-3 flex-wrap">
                    <div>
                        <h1 className="text-amber text-xl font-bold tracking-wider mb-1">
                            {isEdit
                                ? lang === "it" ? "MODIFICA SQUADRA" : "EDIT SQUAD"
                                : lang === "it" ? "NUOVA SQUADRA" : "NEW SQUAD"}
                            {" — "}
                            {meta.titleIt}
                        </h1>
                        <p className="text-[11px] text-muted-foreground tracking-wide">
                            {filledCount}/{meta.size} {lang === "it" ? "membri" : "members"}
                            {" · "}
                            <span className="text-amber font-bold">PWR {totalPower}</span>
                            {warnings.length > 0 && (
                                <span className="ml-3 text-yellow-400" data-testid="squad-warnings">
                                    ⚠ {warnings.join(" · ")}
                                </span>
                            )}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={() => navigate("/squads")}
                            data-testid="squad-cancel-btn"
                            className="px-4 py-2 text-xs tracking-widest border border-neutral-700 hover:border-neutral-500 transition-colors"
                        >
                            {lang === "it" ? "Annulla" : "Cancel"}
                        </button>
                        <button
                            type="button"
                            onClick={save}
                            disabled={saving || !canSave}
                            title={canSave ? "" : saveDisabledReason}
                            data-testid="squad-save-btn"
                            className={`px-4 py-2 text-xs tracking-widest font-bold rounded-sm transition-opacity ${
                                canSave
                                    ? "bg-amber text-background hover:opacity-90"
                                    : "bg-amber/40 text-background/60 cursor-not-allowed opacity-60"
                            } disabled:opacity-40`}
                        >
                            {saving ? "..." : lang === "it" ? "Salva" : "Save"}
                        </button>
                    </div>
                </div>

                <div className="mb-5">
                    <label className="text-[10px] text-muted-foreground tracking-widest block mb-1">
                        {lang === "it" ? "NOME SQUADRA" : "SQUAD NAME"}
                    </label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        maxLength={32}
                        data-testid="squad-name-input"
                        placeholder={lang === "it" ? "Es. Cinque Maledetti" : "e.g. Five Damned"}
                        className="w-full max-w-md bg-secondary border border-neutral-700 px-3 py-2 text-sm focus:border-amber outline-none"
                    />
                </div>

                {/* Search */}
                <div className="mb-3">
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder={
                            lang === "it"
                                ? "Cerca per nome, classe, ruolo, rarità..."
                                : "Search by name, class, role, rarity..."
                        }
                        data-testid="squad-pool-search"
                        className="w-full bg-secondary border border-neutral-700 px-3 py-2 text-xs focus:border-amber outline-none"
                    />
                </div>

                {isRaid ? (
                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                        <div className="lg:col-span-2 border border-neutral-800 rounded-sm p-3">
                            <h3 className="text-amber text-xs font-bold tracking-widest mb-3">
                                :: POOL {lang === "it" ? "AVVENTURIERI" : "ADVENTURERS"} ({filteredPool.length})
                            </h3>
                            <div className="text-[10px] text-muted-foreground mb-2" data-testid="active-party-label">
                                {lang === "it" ? "Click per aggiungere a" : "Click to add to"}:{" "}
                                <select
                                    value={activeParty}
                                    onChange={(e) => setActiveParty(e.target.value)}
                                    data-testid="active-party-select"
                                    className="bg-secondary border border-neutral-700 px-2 py-0.5 text-xs ml-1"
                                >
                                    {["party_1", "party_2", "party_3", "party_4"].map((p) => (
                                        <option key={p} value={p}>
                                            {p.replace("_", " ")} ({parties[p].length}/5)
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="grid grid-cols-1 gap-1 max-h-[600px] overflow-y-auto">
                                {filteredPool.map((a) => (
                                    <AdvChip
                                        key={a.id}
                                        adv={a}
                                        disabled={isAssigned(a.id)}
                                        onClick={() => addToParty(activeParty, a.id)}
                                        testid={`pool-adv-${a.id}`}
                                        action={isAssigned(a.id) ? (lang === "it" ? "(già in raid)" : "(in raid)") : null}
                                    />
                                ))}
                            </div>
                        </div>
                        <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {["party_1", "party_2", "party_3", "party_4"].map((pk) => {
                                const pAdvs = parties[pk].map((aid) => advById[aid]).filter(Boolean);
                                const pPwr = pAdvs.reduce(
                                    (acc, a) => acc + (a.total_power ?? a.base_power ?? 0),
                                    0,
                                );
                                return (
                                    <div
                                        key={pk}
                                        data-testid={`party-slot-${pk}`}
                                        className={`border rounded-sm p-3 ${activeParty === pk ? "border-amber" : "border-neutral-800"}`}
                                    >
                                        <div className="flex justify-between items-baseline mb-2">
                                            <h4 className="text-xs font-bold tracking-widest text-foreground">
                                                {pk.replace("_", " ").toUpperCase()} ({parties[pk].length}/5)
                                            </h4>
                                            <span className="text-[11px] text-amber font-bold">PWR {pPwr}</span>
                                        </div>
                                        <div className="grid grid-cols-1 gap-1">
                                            {pAdvs.length === 0 ? (
                                                <p className="text-[10px] text-muted-foreground italic">
                                                    {lang === "it" ? "Vuoto. Seleziona dal pool." : "Empty. Pick from pool."}
                                                </p>
                                            ) : (
                                                pAdvs.map((a) => (
                                                    <AdvChip
                                                        key={a.id}
                                                        adv={a}
                                                        onClick={() => removeFromParty(pk, a.id)}
                                                        testid={`${pk}-adv-${a.id}`}
                                                        action={lang === "it" ? "Rimuovi" : "Remove"}
                                                    />
                                                ))
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="border border-neutral-800 rounded-sm p-3">
                            <h3 className="text-amber text-xs font-bold tracking-widest mb-3">
                                :: POOL {lang === "it" ? "AVVENTURIERI" : "ADVENTURERS"} ({filteredPool.length})
                            </h3>
                            <div className="grid grid-cols-1 gap-1 max-h-[500px] overflow-y-auto">
                                {filteredPool.map((a) => (
                                    <AdvChip
                                        key={a.id}
                                        adv={a}
                                        disabled={isAssigned(a.id)}
                                        onClick={() => toggleDungeon(a.id)}
                                        testid={`pool-adv-${a.id}`}
                                        action={isAssigned(a.id) ? (lang === "it" ? "(selezionato)" : "(selected)") : null}
                                    />
                                ))}
                            </div>
                        </div>
                        <div className="border border-amber/60 rounded-sm p-3">
                            <h3 className="text-amber text-xs font-bold tracking-widest mb-3">
                                :: SQUADRA ({selected.length}/{meta.size})
                            </h3>
                            <div className="grid grid-cols-1 gap-1">
                                {selected.length === 0 ? (
                                    <p className="text-[10px] text-muted-foreground italic" data-testid="squad-empty-msg">
                                        {lang === "it"
                                            ? "Vuota. Click sugli avventurieri a sinistra."
                                            : "Empty. Click adventurers on the left."}
                                    </p>
                                ) : (
                                    selected
                                        .map((aid) => advById[aid])
                                        .filter(Boolean)
                                        .map((a) => (
                                            <AdvChip
                                                key={a.id}
                                                adv={a}
                                                onClick={() => toggleDungeon(a.id)}
                                                testid={`selected-adv-${a.id}`}
                                                action={lang === "it" ? "Rimuovi" : "Remove"}
                                            />
                                        ))
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
