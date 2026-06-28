import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";
import { TraitList } from "../components/TraitBadge";
import TraitPreviewWidget from "../components/TraitPreviewWidget";
import AdventurerDetailModal from "../components/AdventurerDetailModal";
import AdventurerRenameModal from "../components/AdventurerRenameModal";
import RoleMarker from "../components/RoleMarker";
import { SpecChip } from "../components/SpecializationBadge";

// i18n note (Phase 12.3): stat abbreviations STR / AGI / INT / END / FAI are
// intentionally NOT localized. They follow universal MMO/RPG convention and
// are kept identical across EN/IT to avoid cognitive overhead for players
// switching languages. The same applies to ExpeditionNew.jsx and any other
// place that displays adventurer raw stats.

const RARITY_COLOR = {
    Common: "#9ca3af",
    Uncommon: "#22c55e",
    Rare: "#3b82f6",
    Epic: "#a855f7",
};

const RarityBadge = ({ rarity }) => (
    <span
        className="inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm"
        style={{
            color: RARITY_COLOR[rarity] || RARITY_COLOR.Common,
            borderColor: (RARITY_COLOR[rarity] || RARITY_COLOR.Common) + "55",
        }}
    >
        {rarity?.toUpperCase()}
    </span>
);

const StatusBadge = ({ available }) => (
    <span
        className={`inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm ${
            available
                ? "text-[#22c55e] border-[#22c55e]/55"
                : "text-muted-foreground border-border"
        }`}
        data-testid={`status-${available ? "available" : "busy"}`}
    >
        {available ? "AVAILABLE" : "BUSY"}
    </span>
);

const HEAD = [
    ["Name", "name"],
    ["Class", "class"],
    ["Role", "role"],
    ["Rarity", "rarity"],
    ["Lvl", "level"],
    ["XP", "xp"],
    ["STR", "str"],
    ["AGI", "agi"],
    ["INT", "int"],
    ["END", "end"],
    ["FAI", "fai"],
    ["Power", "power"],
    ["Equip", "equip"],
    ["Traits", "traits"],
    ["Status", "status"],
];

function statBonusBadge(slot, item) {
    if (!item) {
        return (
            <span
                className="inline-block text-[9px] tracking-widest text-muted-foreground border border-border/60 px-1 py-0.5 rounded-sm"
                title={`${slot} empty`}
            >
                {slot[0].toUpperCase()}·—
            </span>
        );
    }
    return (
        <span
            className="inline-block text-[9px] tracking-widest text-amber border border-amber/40 px-1 py-0.5 rounded-sm"
            title={`${slot}: ${item.name}`}
        >
            {slot[0].toUpperCase()}·{item.name}
        </span>
    );
}

const Empty = ({ t }) => (
    <div
        data-testid="adventurers-empty"
        className="border border-border bg-card rounded-sm p-10 text-center"
    >
        <div className="text-amber text-xs tracking-widest mb-2">{t("adventurers.no_heroes")}</div>
        <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
            {t("adventurers.no_adventurers")}
        </p>
        <Link to="/recruitment">
            <Button
                data-testid="goto-recruitment-btn"
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
            >
                {t("adventurers.goto_recruitment")}
            </Button>
        </Link>
    </div>
);

export default function Adventurers() {
    const { t, lang } = useT();
    const [rows, setRows] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState(null);
    const [renaming, setRenaming] = useState(null);
    const [retiring, setRetiring] = useState(null);
    const [retireBusy, setRetireBusy] = useState(false);
    const [retireForceUnequip, setRetireForceUnequip] = useState(false);
    const [retireReason, setRetireReason] = useState("");
    // ROUND 6C — opt-in soft-discard of bound signature item on retire.
    // Required for the backend to accept the retire of a specialized adv.
    const [retireDiscardSignature, setRetireDiscardSignature] = useState(false);

    const openSheet = (a) => setSelected(a);
    const closeSheet = () => setSelected(null);
    const openRename = (a) => setRenaming(a);
    const closeRename = () => setRenaming(null);
    const openRetire = (a) => {
        setRetiring(a);
        setRetireForceUnequip(false);
        setRetireReason("");
        setRetireDiscardSignature(false);
    };
    const closeRetire = () => {
        setRetiring(null);
        setRetireDiscardSignature(false);
    };
    const onRenamed = (updated) => {
        setRows((prev) => (prev || []).map((r) => (r.id === updated.id ? updated : r)));
    };
    const doRetire = async () => {
        if (!retiring) return;
        setRetireBusy(true);
        try {
            await api.post(`/adventurers/${retiring.id}/retire`, {
                reason: retireReason || null,
                force_unequip: retireForceUnequip,
                discard_signature_items: retireDiscardSignature,
            });
            setRows((prev) => (prev || []).filter((r) => r.id !== retiring.id));
            toast.success(`${retiring.name} congedato/a`);
            closeRetire();
        } catch (err) {
            const detail = err?.response?.data?.detail;
            const code = detail?.code;
            if (code === "adventurer.in_expedition") {
                toast.error(detail.user_message || "Avventuriero impegnato in una spedizione/raid attivo.");
            } else if (code === "adventurer.in_squad") {
                const squadNames = (detail.squads || []).map((s) => s.name).join(", ");
                toast.error(`Rimuovi prima dalle squadre: ${squadNames}`);
            } else if (code === "adventurer.equipped") {
                toast.error(`${detail.equipped_count} oggetti equipaggiati. Spunta "Disequipaggia e congeda" per procedere.`);
            } else if (code === "adventurer.already_retired") {
                toast.warning("Avventuriero già congedato");
            } else if (code === "retire.bound_item_blocks_retirement" || code === "adventurer.has_bound_items") {
                toast.error(detail.user_message || "L'avventuriero ha un signature item legato — spunta 'Distruggi signature item' per congedare.");
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setRetireBusy(false);
        }
    };

    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get("/adventurers");
                setRows(data.adventurers);
            } catch (err) {
                toast.error(formatApiError(err));
                setRows([]);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.adventurers" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="mb-6">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        {t("adventurers.guild_roster")}
                    </div>
                    <div className="flex items-end justify-between gap-3 flex-wrap">
                        <div>
                            <h1 className="text-3xl font-semibold tracking-tight">
                                {t("adventurers.title")}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                                {t("adventurers.subtitle")}
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-[10px] text-muted-foreground tracking-widest">
                                TOTAL
                            </div>
                            <div
                                data-testid="adventurer-count"
                                className="text-2xl font-semibold text-amber"
                            >
                                {rows?.length ?? "—"}
                            </div>
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="border border-border bg-card rounded-sm p-6 text-xs text-muted-foreground">
                        {t("common.loading")}<span className="caret-blink" />
                    </div>
                )}

                {!loading && rows && rows.length === 0 && <Empty t={t} />}

                {!loading && rows && rows.length > 0 && (
                    <>
                        {/* Desktop / tablet table */}
                        <div className="hidden sm:block border border-border rounded-sm overflow-x-auto">
                            <table
                                data-testid="adventurers-table"
                                className="w-full text-sm min-w-[760px]"
                            >
                                <thead className="bg-secondary/40 text-[10px] text-muted-foreground tracking-widest">
                                    <tr>
                                        {HEAD.map(([label, k]) => (
                                            <th
                                                key={k}
                                                className="text-left px-3 py-2 font-normal border-b border-border whitespace-nowrap"
                                            >
                                                {label.toUpperCase()}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.map((a) => (
                                        <tr
                                            key={a.id}
                                            data-testid={`adventurer-row-${a.id}`}
                                            className="border-b border-border/60 hover:bg-secondary/20 cursor-pointer"
                                            onClick={() => openSheet(a)}
                                        >
                                            <td className="px-3 py-2 whitespace-nowrap font-medium">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <button
                                                        type="button"
                                                        data-testid={`adventurer-name-${a.id}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            openSheet(a);
                                                        }}
                                                        className="text-left hover:text-amber focus-visible:outline-none focus-visible:text-amber"
                                                        title={t("adventurer_modal.open_sheet")}
                                                    >
                                                        {a.name}
                                                    </button>
                                                    <SpecChip
                                                        spec={a.specialization}
                                                        lang={lang}
                                                        testid={`adventurer-spec-chip-${a.id}`}
                                                    />
                                                </div>
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                                                {a.class_name}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                                                <RoleMarker role={a.class_role} withLabel />
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap">
                                                <RarityBadge rarity={a.rarity} />
                                            </td>
                                            <td className="px-3 py-2">{a.level}</td>
                                            <td className="px-3 py-2 text-muted-foreground">
                                                {a.experience}
                                            </td>
                                            <td className="px-3 py-2">{a.strength}</td>
                                            <td className="px-3 py-2">{a.agility}</td>
                                            <td className="px-3 py-2">{a.intellect}</td>
                                            <td className="px-3 py-2">{a.endurance}</td>
                                            <td className="px-3 py-2">{a.faith}</td>
                                            <td className="px-3 py-2 whitespace-nowrap">
                                                <span className="text-amber font-medium" data-testid={`adv-power-${a.id}`}>
                                                    {a.total_power}
                                                </span>
                                                {a.equipment_power > 0 && (
                                                    <span className="text-[10px] text-muted-foreground ml-1">
                                                        ({a.base_power}+{a.equipment_power})
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                                                <div className="flex flex-col gap-1">
                                                    <Link
                                                        to={`/adventurers/${a.id}/equipment`}
                                                        data-testid={`equip-link-${a.id}`}
                                                        className="text-[11px] text-amber hover:underline"
                                                    >
                                                        {t("adventurers.manage")}
                                                    </Link>
                                                    <button
                                                        type="button"
                                                        data-testid={`rename-btn-${a.id}`}
                                                        onClick={() => openRename(a)}
                                                        disabled={(a.renames_remaining ?? 2) <= 0}
                                                        title={
                                                            (a.renames_remaining ?? 2) <= 0
                                                                ? "Limite rinomine raggiunto (2/2)"
                                                                : `Rinomine rimaste: ${a.renames_remaining ?? 2}/2`
                                                        }
                                                        className="text-[11px] text-muted-foreground hover:text-amber disabled:opacity-30 disabled:cursor-not-allowed text-left"
                                                    >
                                                        ✎ rinomina ({a.renames_remaining ?? 2}/2)
                                                    </button>
                                                    <button
                                                        type="button"
                                                        data-testid={`adventurer-retire-btn-${a.id}`}
                                                        onClick={() => openRetire(a)}
                                                        className="text-[11px] text-muted-foreground hover:text-red-400 text-left"
                                                        title="Congeda l'avventuriero (soft retire)"
                                                    >
                                                        ⊘ congeda
                                                    </button>
                                                </div>
                                            </td>
                                            <td className="px-3 py-2 min-w-[160px]" onClick={(e) => e.stopPropagation()}>
                                                <TraitList traits={a.traits} />
                                                {a.traits && a.traits.length > 0 && (
                                                    <TraitPreviewWidget
                                                        adventurerId={a.id}
                                                        hasTraits={true}
                                                    />
                                                )}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap">
                                                <StatusBadge available={a.is_available} />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Mobile stacked cards */}
                        <div className="sm:hidden space-y-3" data-testid="adventurers-cards">
                            {rows.map((a) => (
                                <div
                                    key={a.id}
                                    data-testid={`adventurer-card-${a.id}`}
                                    role="button"
                                    tabIndex={0}
                                    onClick={() => openSheet(a)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter" || e.key === " ") {
                                            e.preventDefault();
                                            openSheet(a);
                                        }
                                    }}
                                    className="border border-border bg-card rounded-sm p-4 cursor-pointer hover:border-amber/40 focus-visible:outline-none focus-visible:border-amber/60"
                                >
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <div className="min-w-0">
                                            <div className="font-medium truncate flex items-center gap-2 flex-wrap">
                                                <span>{a.name}</span>
                                                <SpecChip
                                                    spec={a.specialization}
                                                    lang={lang}
                                                    testid={`adventurer-spec-chip-mobile-${a.id}`}
                                                />
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                {a.class_name} · {a.class_role}
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-1">
                                            <RarityBadge rarity={a.rarity} />
                                            <StatusBadge available={a.is_available} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs mt-3">
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">LVL</span>
                                            <span>{a.level}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">XP</span>
                                            <span>{a.experience}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">STR</span>
                                            <span>{a.strength}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">AGI</span>
                                            <span>{a.agility}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">INT</span>
                                            <span>{a.intellect}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">END</span>
                                            <span>{a.endurance}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">FAI</span>
                                            <span>{a.faith}</span>
                                        </div>
                                    </div>
                                    {a.traits && a.traits.length > 0 && (
                                        <div className="mt-3 pt-3 border-t border-border/60">
                                            <div className="text-[10px] text-muted-foreground tracking-widest mb-1.5">
                                                TRAITS
                                            </div>
                                            <TraitList traits={a.traits} />
                                            <TraitPreviewWidget
                                                adventurerId={a.id}
                                                hasTraits={true}
                                            />
                                        </div>
                                    )}
                                    <div className="mt-3 pt-3 border-t border-border/60" onClick={(e) => e.stopPropagation()}>
                                        <div className="text-[10px] text-muted-foreground tracking-widest mb-1.5">
                                            EQUIPMENT · POWER {a.total_power}
                                            {a.equipment_power > 0 && (
                                                <span className="text-amber"> (+{a.equipment_power})</span>
                                            )}
                                        </div>
                                        <div className="flex flex-wrap gap-1 mb-2">
                                            {statBonusBadge("weapon", a.equipment?.weapon?.item)}
                                            {statBonusBadge("armor", a.equipment?.armor?.item)}
                                            {statBonusBadge("accessory", a.equipment?.accessory?.item)}
                                        </div>
                                        <Link
                                            to={`/adventurers/${a.id}/equipment`}
                                            data-testid={`equip-link-mobile-${a.id}`}
                                            className="text-[11px] text-amber hover:underline"
                                        >
                                            {t("adventurers.manage_equipment")}
                                        </Link>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </main>

            <AdventurerDetailModal adventurer={selected} onClose={closeSheet} />
            <AdventurerRenameModal adventurer={renaming} onClose={closeRename} onRenamed={onRenamed} />
            {retiring && (
                <div
                    data-testid="adventurer-retire-modal"
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
                    onClick={closeRetire}
                >
                    <div
                        className="bg-card border border-border rounded-sm max-w-md w-full p-6"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-base font-bold tracking-widest mb-2" data-testid="adventurer-retire-modal-title">
                            CONGEDA AVVENTURIERO
                        </h3>
                        <div className="text-sm mb-3">
                            <div className="text-foreground font-bold flex items-center gap-2 flex-wrap">
                                <span>{retiring.name}</span>
                                <SpecChip
                                    spec={retiring.specialization}
                                    lang={lang}
                                    testid="adventurer-retire-modal-spec-chip"
                                />
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                {retiring.class_name} · {retiring.role || retiring.class_role || "—"} · Lv{retiring.level} · PWR {retiring.total_power ?? retiring.power}
                            </div>
                        </div>
                        <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
                            Il congedo è soft: lo storico delle spedizioni resta, lo slot del roster viene liberato.
                            L&apos;avventuriero non sarà più selezionabile.
                        </p>
                        {retiring.specialization && (
                            <div
                                data-testid="adventurer-retire-modal-signature-warning"
                                className="border border-red-500/60 bg-red-500/10 rounded-sm p-3 mb-3 text-[11px]"
                            >
                                <div className="text-red-300 font-bold tracking-widest mb-2">
                                    {t("adventurers_retire.signature_warning_title")}
                                </div>
                                <p className="text-foreground/80 mb-2 leading-relaxed">
                                    {t("adventurers_retire.signature_warning_body", {
                                        spec: (lang === "it"
                                            ? retiring.specialization.name_it
                                            : retiring.specialization.name_en) || retiring.specialization.slug,
                                        item: t("specialization.signature_label", "signature item"),
                                    })}
                                </p>
                                <label className="flex items-start gap-2 cursor-pointer">
                                    <input
                                        data-testid="adventurer-retire-modal-discard-signature"
                                        type="checkbox"
                                        checked={retireDiscardSignature}
                                        onChange={(e) => setRetireDiscardSignature(e.target.checked)}
                                        className="accent-red-500 mt-0.5"
                                    />
                                    <span className="text-foreground/90">
                                        {t("adventurers_retire.discard_signature_label", {
                                            item: t("specialization.signature_label", "signature item"),
                                        })}
                                    </span>
                                </label>
                                <p className="text-[10px] text-muted-foreground mt-2">
                                    {t("adventurers_retire.discard_signature_hint")}
                                </p>
                            </div>
                        )}
                        <label className="flex items-center gap-2 text-[11px] mb-3 cursor-pointer">
                            <input
                                type="checkbox"
                                data-testid="adventurer-retire-modal-force-unequip"
                                checked={retireForceUnequip}
                                onChange={(e) => setRetireForceUnequip(e.target.checked)}
                                className="accent-amber"
                            />
                            <span>Disequipaggia automaticamente se ha oggetti attivi</span>
                        </label>
                        <input
                            type="text"
                            data-testid="adventurer-retire-modal-reason"
                            placeholder="Motivo (opzionale)"
                            value={retireReason}
                            onChange={(e) => setRetireReason(e.target.value)}
                            maxLength={200}
                            className="w-full mb-4 px-3 py-2 text-xs bg-background border border-border rounded-sm focus:outline-none focus:border-amber"
                        />
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={closeRetire}
                                disabled={retireBusy}
                                data-testid="adventurer-retire-modal-cancel"
                                className="flex-1 px-3 py-2 text-[11px] tracking-widest border border-border text-muted-foreground hover:text-foreground transition-colors rounded-sm"
                            >
                                ANNULLA
                            </button>
                            <button
                                type="button"
                                onClick={doRetire}
                                disabled={retireBusy || (retiring.specialization && !retireDiscardSignature)}
                                data-testid="adventurer-retire-modal-confirm"
                                className="flex-1 px-3 py-2 text-[11px] tracking-widest font-bold bg-red-500/80 text-white hover:bg-red-500 transition-colors rounded-sm disabled:opacity-50"
                            >
                                {retireBusy ? "..." : "CONFERMA"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
