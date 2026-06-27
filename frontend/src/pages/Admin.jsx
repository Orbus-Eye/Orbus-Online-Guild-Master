import { useEffect, useState, useCallback } from "react";
/* eslint-disable react/jsx-key -- cells returned from renderRow() are wrapped in keyed <td> elements below */
import { Navigate } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "../components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "../components/ui/select";

const TABS = [
    { key: "classes", label: "CLASSES" },
    { key: "traits", label: "TRAITS" },
    { key: "dungeons", label: "DUNGEONS" },
    { key: "items", label: "ITEMS" },
];

const ActiveBadge = ({ active }) => (
    <span
        data-testid={`active-${active}`}
        className={`inline-block text-[10px] tracking-widest border px-1.5 py-0.5 rounded-sm ${
            active
                ? "text-[#22c55e] border-[#22c55e]/55"
                : "text-muted-foreground border-border"
        }`}
    >
        {active ? "ACTIVE" : "INACTIVE"}
    </span>
);

// ─── Generic editor field components ──────────────────────────────────────────
const TextField = ({ label, value, onChange, testid, required, ...rest }) => (
    <div className="space-y-1.5">
        <Label className="text-[10px] text-muted-foreground tracking-widest">
            {label}
            {required && <span className="text-amber"> *</span>}
        </Label>
        <Input
            data-testid={testid}
            value={value ?? ""}
            onChange={(e) => onChange(e.target.value)}
            className="bg-background border-border rounded-sm h-10 font-mono text-base"
            {...rest}
        />
    </div>
);

const NumField = ({ label, value, onChange, testid, min, max }) => (
    <div className="space-y-1.5">
        <Label className="text-[10px] text-muted-foreground tracking-widest">
            {label}
        </Label>
        <Input
            type="number"
            min={min}
            max={max}
            data-testid={testid}
            value={value ?? 0}
            onChange={(e) => onChange(Number(e.target.value))}
            className="bg-background border-border rounded-sm h-10 font-mono text-base"
        />
    </div>
);

const CheckField = ({ label, checked, onChange, testid }) => (
    <label className="flex items-center gap-2 cursor-pointer">
        <input
            type="checkbox"
            data-testid={testid}
            checked={!!checked}
            onChange={(e) => onChange(e.target.checked)}
            className="accent-[#d4a14a] w-4 h-4"
        />
        <span className="text-xs">{label}</span>
    </label>
);

const SelectField = ({ label, value, onChange, options, testid }) => (
    <div className="space-y-1.5">
        <Label className="text-[10px] text-muted-foreground tracking-widest">
            {label}
        </Label>
        <Select value={value || ""} onValueChange={onChange}>
            <SelectTrigger
                data-testid={testid}
                className="bg-background border-border rounded-sm h-10 font-mono text-base"
            >
                <SelectValue placeholder="select…" />
            </SelectTrigger>
            <SelectContent>
                {options.map((o) => (
                    <SelectItem key={o} value={o}>
                        {o}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    </div>
);

// ─── Editor configs per entity ────────────────────────────────────────────────
function ClassEditor({ form, set }) {
    const { t } = useT();
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TextField label="Name" value={form.name} onChange={(v) => set("name", v)} testid="field-name" required />
            <TextField label="Slug" value={form.slug} onChange={(v) => set("slug", v.toLowerCase())} testid="field-slug" required placeholder="warrior" />
            <SelectField label="Role" value={form.role} onChange={(v) => set("role", v)} options={["Tank", "DPS", "Healer"]} testid="field-role" />
            <CheckField label="Active" checked={form.is_active ?? true} onChange={(v) => set("is_active", v)} testid="field-active" />
            <div className="sm:col-span-2">
                <Label className="text-[10px] text-muted-foreground tracking-widest">{t("admin_extra.label_description")}</Label>
                <Textarea data-testid="field-description" value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} className="bg-background border-border rounded-sm font-mono text-base mt-1.5" />
            </div>
            <NumField label="Base STR" value={form.base_strength} onChange={(v) => set("base_strength", v)} testid="field-str" min={0} max={15} />
            <NumField label="Base AGI" value={form.base_agility} onChange={(v) => set("base_agility", v)} testid="field-agi" min={0} max={15} />
            <NumField label="Base INT" value={form.base_intellect} onChange={(v) => set("base_intellect", v)} testid="field-int" min={0} max={15} />
            <NumField label="Base END" value={form.base_endurance} onChange={(v) => set("base_endurance", v)} testid="field-end" min={0} max={15} />
            <NumField label="Base FAITH" value={form.base_faith} onChange={(v) => set("base_faith", v)} testid="field-faith" min={0} max={15} />
        </div>
    );
}

function TraitEditor({ form, set }) {
    const { t } = useT();
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TextField label="Name" value={form.name} onChange={(v) => set("name", v)} testid="field-name" required />
            <CheckField label="Active" checked={form.is_active ?? true} onChange={(v) => set("is_active", v)} testid="field-active" />
            <div className="sm:col-span-2">
                <Label className="text-[10px] text-muted-foreground tracking-widest">{t("admin_extra.label_description")}</Label>
                <Textarea data-testid="field-description" value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} className="bg-background border-border rounded-sm font-mono text-base mt-1.5" />
            </div>
            <SelectField label="Modifier Type" value={form.modifier_type} onChange={(v) => set("modifier_type", v)} options={["flat", "percent"]} testid="field-modtype" />
            <SelectField label="Affected Stat" value={form.affected_stat} onChange={(v) => set("affected_stat", v)} options={["strength", "agility", "intellect", "endurance", "faith", "xp_gain"]} testid="field-stat" />
            <NumField label="Modifier Value" value={form.modifier_value} onChange={(v) => set("modifier_value", v)} testid="field-modvalue" />
            <CheckField label="Positive" checked={form.is_positive ?? true} onChange={(v) => set("is_positive", v)} testid="field-positive" />
        </div>
    );
}

function DungeonEditor({ form, set }) {
    const { t } = useT();
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TextField label="Name" value={form.name} onChange={(v) => set("name", v)} testid="field-name" required />
            <TextField label="Slug" value={form.slug} onChange={(v) => set("slug", v.toLowerCase())} testid="field-slug" required />
            <div className="sm:col-span-2">
                <Label className="text-[10px] text-muted-foreground tracking-widest">{t("admin_extra.label_description")}</Label>
                <Textarea data-testid="field-description" value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} className="bg-background border-border rounded-sm font-mono text-base mt-1.5" />
            </div>
            <NumField label="Difficulty" value={form.difficulty} onChange={(v) => set("difficulty", v)} testid="field-difficulty" min={1} />
            <NumField label="Team size" value={form.required_team_size} onChange={(v) => set("required_team_size", v)} testid="field-team-size" min={1} />
            <NumField label="Duration (s)" value={form.base_duration_seconds} onChange={(v) => set("base_duration_seconds", v)} testid="field-duration" min={10} />
            <NumField label="Rec. power" value={form.recommended_power} onChange={(v) => set("recommended_power", v)} testid="field-recpower" min={0} />
            <NumField label="Gold reward" value={form.base_gold_reward} onChange={(v) => set("base_gold_reward", v)} testid="field-gold" min={0} />
            <NumField label="XP reward" value={form.base_xp_reward} onChange={(v) => set("base_xp_reward", v)} testid="field-xp" min={0} />
            <CheckField label="Active" checked={form.is_active ?? true} onChange={(v) => set("is_active", v)} testid="field-active" />
        </div>
    );
}

function ItemEditor({ form, set }) {
    const { t } = useT();
    const realMoney = !!form.can_be_sold_for_real_money;
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TextField label="Name" value={form.name} onChange={(v) => set("name", v)} testid="field-name" required />
            <TextField label="Slug" value={form.slug} onChange={(v) => set("slug", v.toLowerCase())} testid="field-slug" required />
            <div className="sm:col-span-2">
                <Label className="text-[10px] text-muted-foreground tracking-widest">{t("admin_extra.label_description")}</Label>
                <Textarea data-testid="field-description" value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} className="bg-background border-border rounded-sm font-mono text-base mt-1.5" />
            </div>
            <SelectField label="Type" value={form.item_type} onChange={(v) => set("item_type", v)} options={["weapon", "armor", "accessory", "consumable"]} testid="field-type" />
            <SelectField label="Rarity" value={form.rarity} onChange={(v) => set("rarity", v)} options={["Common", "Uncommon", "Rare", "Epic"]} testid="field-rarity" />
            <NumField label="Level required" value={form.level_required} onChange={(v) => set("level_required", v)} testid="field-level-req" min={1} />
            <NumField label="Power score" value={form.power_score} onChange={(v) => set("power_score", v)} testid="field-power" min={0} />
            <NumField label="STR bonus" value={form.strength_bonus} onChange={(v) => set("strength_bonus", v)} testid="field-str-bonus" />
            <NumField label="AGI bonus" value={form.agility_bonus} onChange={(v) => set("agility_bonus", v)} testid="field-agi-bonus" />
            <NumField label="INT bonus" value={form.intellect_bonus} onChange={(v) => set("intellect_bonus", v)} testid="field-int-bonus" />
            <NumField label="END bonus" value={form.endurance_bonus} onChange={(v) => set("endurance_bonus", v)} testid="field-end-bonus" />
            <NumField label="FAITH bonus" value={form.faith_bonus} onChange={(v) => set("faith_bonus", v)} testid="field-faith-bonus" />
            <div className="sm:col-span-2 border-t border-border pt-3 mt-2 grid grid-cols-2 gap-2">
                <CheckField label="Tradeable" checked={form.is_tradeable ?? true} onChange={(v) => set("is_tradeable", v)} testid="field-tradeable" />
                <CheckField label="Cosmetic" checked={form.is_cosmetic ?? false} onChange={(v) => {
                    set("is_cosmetic", v);
                    if (!v) set("can_be_sold_for_real_money", false);
                }} testid="field-cosmetic" />
                <CheckField label="Affects combat" checked={form.affects_combat ?? true} onChange={(v) => {
                    set("affects_combat", v);
                    if (v) set("can_be_sold_for_real_money", false);
                }} testid="field-affects-combat" />
                <CheckField label="Affects economy" checked={form.affects_economy ?? false} onChange={(v) => {
                    set("affects_economy", v);
                    if (v) set("can_be_sold_for_real_money", false);
                }} testid="field-affects-economy" />
                <CheckField label="Affects ranking" checked={form.affects_ranking ?? false} onChange={(v) => {
                    set("affects_ranking", v);
                    if (v) set("can_be_sold_for_real_money", false);
                }} testid="field-affects-ranking" />
                <CheckField label="Sellable for gold" checked={form.can_be_sold_for_gold ?? true} onChange={(v) => set("can_be_sold_for_gold", v)} testid="field-sell-gold" />
                <CheckField label="Real-money sale" checked={realMoney} onChange={(v) => {
                    set("can_be_sold_for_real_money", v);
                    if (v) {
                        set("is_cosmetic", true);
                        set("affects_combat", false);
                        set("affects_economy", false);
                        set("affects_ranking", false);
                    }
                }} testid="field-sell-realmoney" />
                <CheckField label="Active" checked={form.is_active ?? true} onChange={(v) => set("is_active", v)} testid="field-active" />
            </div>
            {realMoney && (
                <div
                    data-testid="realmoney-warning"
                    className="sm:col-span-2 text-xs text-amber border border-amber/40 bg-amber/5 px-3 py-2 rounded-sm"
                >
                    ⚠ Real-money sale requires cosmetic-only items (no combat/economy/ranking impact). These flags have been auto-cleared.
                </div>
            )}
        </div>
    );
}

const TAB_CONFIG = {
    classes: {
        endpoint: "/admin/classes",
        listKey: "classes",
        singleKey: "class",
        Editor: ClassEditor,
        emptyForm: () => ({
            name: "", slug: "", role: "DPS", description: "",
            base_strength: 5, base_agility: 5, base_intellect: 5,
            base_endurance: 5, base_faith: 5, is_active: true,
        }),
        columns: ["Name", "Slug", "Role", "Stats", "Active"],
        renderRow: (r) => [
            r.name,
            <span className="text-muted-foreground font-mono text-xs">{r.slug}</span>,
            r.role,
            <span className="text-xs font-mono">{r.base_strength}/{r.base_agility}/{r.base_intellect}/{r.base_endurance}/{r.base_faith}</span>,
            <ActiveBadge active={r.is_active} />,
        ],
    },
    traits: {
        endpoint: "/admin/traits",
        listKey: "traits",
        singleKey: "trait",
        Editor: TraitEditor,
        emptyForm: () => ({
            name: "", description: "", modifier_type: "flat",
            affected_stat: "strength", modifier_value: 1, is_positive: true,
            is_active: true,
        }),
        columns: ["Name", "Modifier", "Stat", "Value", "Pos.", "Active"],
        renderRow: (r) => [
            r.name,
            r.modifier_type,
            r.affected_stat,
            <span className={r.modifier_value < 0 ? "text-[#ef4444]" : "text-[#22c55e]"}>
                {r.modifier_value > 0 ? `+${r.modifier_value}` : r.modifier_value}
            </span>,
            r.is_positive ? "✓" : "✗",
            <ActiveBadge active={r.is_active} />,
        ],
    },
    dungeons: {
        endpoint: "/admin/dungeons",
        listKey: "dungeons",
        singleKey: "dungeon",
        Editor: DungeonEditor,
        emptyForm: () => ({
            name: "", slug: "", description: "", difficulty: 1,
            required_team_size: 3, base_duration_seconds: 60,
            recommended_power: 45, base_gold_reward: 35, base_xp_reward: 25,
            is_active: true,
        }),
        columns: ["Name", "Slug", "Diff", "Team", "Reward", "Active"],
        renderRow: (r) => [
            r.name,
            <span className="text-muted-foreground font-mono text-xs">{r.slug}</span>,
            r.difficulty,
            r.required_team_size,
            <span className="text-amber">{r.base_gold_reward}g</span>,
            <ActiveBadge active={r.is_active} />,
        ],
    },
    items: {
        endpoint: "/admin/items",
        listKey: "items",
        singleKey: "item",
        Editor: ItemEditor,
        emptyForm: () => ({
            name: "", slug: "", description: "", item_type: "weapon",
            rarity: "Common", level_required: 1, power_score: 5,
            strength_bonus: 0, agility_bonus: 0, intellect_bonus: 0,
            endurance_bonus: 0, faith_bonus: 0,
            is_tradeable: true, is_cosmetic: false, affects_combat: true,
            affects_economy: false, affects_ranking: false,
            can_be_sold_for_gold: true, can_be_sold_for_real_money: false,
            is_active: true,
        }),
        columns: ["Name", "Type", "Rarity", "Power", "Real$", "Active"],
        renderRow: (r) => [
            r.name,
            r.item_type,
            r.rarity,
            r.power_score,
            r.can_be_sold_for_real_money ? "✓" : "—",
            <ActiveBadge active={r.is_active} />,
        ],
    },
};

export default function Admin() {
    const { t } = useT();
    const { user } = useAuth();
    const [tab, setTab] = useState("classes");
    const [rows, setRows] = useState({});
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(null); // row object or {__new: true}
    const [form, setForm] = useState({});
    const [saving, setSaving] = useState(false);

    const cfg = TAB_CONFIG[tab];

    const fetchTab = useCallback(async (t) => {
        const c = TAB_CONFIG[t];
        try {
            const { data } = await api.get(c.endpoint);
            setRows((prev) => ({ ...prev, [t]: data[c.listKey] }));
        } catch (err) {
            toast.error(formatApiError(err));
        }
    }, []);

    useEffect(() => {
        if (user?.is_admin) {
            setLoading(true);
            Promise.all(Object.keys(TAB_CONFIG).map(fetchTab)).finally(() => setLoading(false));
        }
    }, [user, fetchTab]);

    if (user && !user.is_admin) {
        toast.error(t("admin_extra.toast_admin_required"));
        return <Navigate to="/dashboard" replace />;
    }
    if (!user) return null;

    const startCreate = () => {
        setEditing({ __new: true });
        setForm(cfg.emptyForm());
    };

    const startEdit = (row) => {
        setEditing(row);
        setForm({ ...row });
    };

    const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

    const submit = async () => {
        setSaving(true);
        try {
            if (editing.__new) {
                await api.post(cfg.endpoint, form);
                toast.success(t("admin_extra.toast_created"));
            } else {
                await api.patch(`${cfg.endpoint}/${editing.id}`, form);
                toast.success(t("admin_extra.toast_updated"));
            }
            await fetchTab(tab);
            setEditing(null);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setSaving(false);
        }
    };

    const toggleActive = async (row) => {
        try {
            await api.post(`${cfg.endpoint}/${row.id}/toggle-active`);
            await fetchTab(tab);
        } catch (err) {
            toast.error(formatApiError(err));
        }
    };

    const currentRows = rows[tab] || [];

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.admin" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="flex items-end justify-between gap-3 mb-6 flex-wrap">
                    <div>
                        <div className="text-xs text-amber tracking-widest mb-2">
                            :: ADMIN CONSOLE
                        </div>
                        <h1 className="text-3xl font-semibold tracking-tight">{t("admin_extra.h1")}</h1>
                        <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                            Manage game content. Changes are immediate and apply to all guilds.
                        </p>
                    </div>
                    <Button
                        data-testid="admin-new-btn"
                        onClick={startCreate}
                        className="h-10 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                        + New
                    </Button>
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-1 mb-5 border-b border-border overflow-x-auto">
                    {TABS.map((t) => (
                        <button
                            key={t.key}
                            data-testid={`admin-tab-${t.key}`}
                            onClick={() => setTab(t.key)}
                            className={`px-4 py-2 text-xs tracking-widest border-b-2 transition-colors whitespace-nowrap ${
                                tab === t.key
                                    ? "border-amber text-amber"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                            }`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {loading && (
                    <div className="text-xs text-muted-foreground">
                        loading<span className="caret-blink" />
                    </div>
                )}

                {!loading && (
                    <>
                        {/* Desktop table */}
                        <div className="hidden sm:block border border-border rounded-sm overflow-x-auto">
                            <table data-testid={`admin-table-${tab}`} className="w-full text-sm min-w-[600px]">
                                <thead className="bg-secondary/40 text-[10px] text-muted-foreground tracking-widest">
                                    <tr>
                                        {cfg.columns.map((c) => (
                                            <th key={c} className="text-left px-3 py-2 font-normal border-b border-border whitespace-nowrap">
                                                {c.toUpperCase()}
                                            </th>
                                        ))}
                                        <th className="text-right px-3 py-2 font-normal border-b border-border" />
                                    </tr>
                                </thead>
                                <tbody>
                                    {currentRows.map((r) => (
                                        <tr
                                            key={r.id}
                                            data-testid={`admin-row-${r.id}`}
                                            className="border-b border-border/60 hover:bg-secondary/20"
                                        >
                                            {cfg.renderRow(r).map((cell, i) => (
                                                <td key={`${r.id}-${cfg.columns[i] || i}`} className="px-3 py-2 whitespace-nowrap">
                                                    {cell}
                                                </td>
                                            ))}
                                            <td className="px-3 py-2 text-right whitespace-nowrap">
                                                <button
                                                    onClick={() => startEdit(r)}
                                                    data-testid={`admin-edit-${r.id}`}
                                                    className="text-xs text-amber hover:underline mr-3"
                                                >
                                                    edit
                                                </button>
                                                <button
                                                    onClick={() => toggleActive(r)}
                                                    data-testid={`admin-toggle-${r.id}`}
                                                    className="text-xs text-muted-foreground hover:text-foreground"
                                                >
                                                    toggle
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Mobile cards */}
                        <div className="sm:hidden space-y-3" data-testid={`admin-cards-${tab}`}>
                            {currentRows.map((r) => (
                                <div
                                    key={r.id}
                                    data-testid={`admin-card-${r.id}`}
                                    className="border border-border bg-card rounded-sm p-4"
                                >
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <div className="font-medium truncate">{r.name}</div>
                                        <ActiveBadge active={r.is_active} />
                                    </div>
                                    <div className="text-xs text-muted-foreground mb-3">
                                        {r.slug || ""}
                                    </div>
                                    <div className="flex gap-3 text-xs">
                                        <button onClick={() => startEdit(r)} data-testid={`admin-edit-${r.id}`} className="text-amber">edit</button>
                                        <button onClick={() => toggleActive(r)} data-testid={`admin-toggle-${r.id}`} className="text-muted-foreground">toggle</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </main>

            {/* Editor dialog */}
            <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
                <DialogContent className="bg-card border-border max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="admin-editor-dialog">
                    <DialogHeader>
                        <DialogTitle className="text-amber tracking-widest text-sm">
                            :: {editing?.__new ? "NEW" : "EDIT"} {tab.toUpperCase()}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="py-4">
                        {editing && <cfg.Editor form={form} set={set} />}
                    </div>
                    <DialogFooter className="gap-2">
                        <Button
                            variant="outline"
                            onClick={() => setEditing(null)}
                            data-testid="admin-cancel-btn"
                            className="border-border bg-transparent hover:bg-secondary"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={submit}
                            disabled={saving}
                            data-testid="admin-save-btn"
                            className="bg-primary text-primary-foreground hover:bg-primary/90"
                        >
                            {saving ? "saving…" : "Save"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
