import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

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
    ["Status", "status"],
];

const Empty = () => (
    <div
        data-testid="adventurers-empty"
        className="border border-border bg-card rounded-sm p-10 text-center"
    >
        <div className="text-amber text-xs tracking-widest mb-2">:: NO HEROES YET</div>
        <p className="text-sm text-muted-foreground mb-5 max-w-md mx-auto">
            No adventurers yet. Visit Recruitment to hire your first hero.
        </p>
        <Link to="/recruitment">
            <Button
                data-testid="goto-recruitment-btn"
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
            >
                Go to Recruitment →
            </Button>
        </Link>
    </div>
);

export default function Adventurers() {
    const [rows, setRows] = useState(null);
    const [loading, setLoading] = useState(true);

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
            <AppHeader subtitle="ROSTER" />

            <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="mb-6">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: GUILD ROSTER
                    </div>
                    <div className="flex items-end justify-between gap-3 flex-wrap">
                        <div>
                            <h1 className="text-3xl font-semibold tracking-tight">
                                Adventurers
                            </h1>
                            <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                                Every hero hired by your guild. Stats reflect class base ±
                                rolled variance.
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
                        loading roster<span className="caret-blink" />
                    </div>
                )}

                {!loading && rows && rows.length === 0 && <Empty />}

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
                                            className="border-b border-border/60 hover:bg-secondary/20"
                                        >
                                            <td className="px-3 py-2 whitespace-nowrap font-medium">
                                                {a.name}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                                                {a.class_name}
                                            </td>
                                            <td className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                                                {a.class_role}
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
                                    className="border border-border bg-card rounded-sm p-4"
                                >
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <div className="min-w-0">
                                            <div className="font-medium truncate">{a.name}</div>
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
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
