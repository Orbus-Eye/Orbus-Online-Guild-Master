// Phase 16 — Consortiums page (MVP).
import { useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import AppHeader from "../components/AppHeader";
import { toast } from "sonner";


export default function Consortiums() {
    const { user, guild } = useAuth();
    const { t } = useT();
    const [list, setList] = useState([]);
    const [mine, setMine] = useState(null);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(null);
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({ name: "", tag: "", description: "" });

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [{ data: a }, { data: b }] = await Promise.all([
                api.get("/consortiums?limit=50"),
                api.get("/consortiums/me"),
            ]);
            setList(a.consortiums || []);
            setMine(b.consortium || null);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (user && guild) load();
    }, [user, guild, load]);

    if (!user || !guild) return null;

    const onCreate = async (e) => {
        e.preventDefault();
        setBusy("create");
        try {
            await api.post("/consortiums", form);
            toast.success(t("consortiums.create_success"));
            setShowCreate(false);
            setForm({ name: "", tag: "", description: "" });
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(null);
        }
    };

    const onJoin = async (cid) => {
        setBusy(`join-${cid}`);
        try {
            await api.post(`/consortiums/${cid}/join`);
            toast.success(t("consortiums.join_success"));
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(null);
        }
    };

    const onLeave = async () => {
        setBusy("leave");
        try {
            await api.post("/consortiums/leave");
            toast.success(t("consortiums.leave_success"));
            await load();
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(null);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-5xl mx-auto px-4 py-6 font-mono">
                <header className="mb-6 flex items-baseline justify-between gap-3 flex-wrap">
                    <div>
                        <h1
                            data-testid="consortiums-title"
                            className="text-amber text-xl tracking-widest"
                        >
                            :: {t("consortiums.title")}
                        </h1>
                        <p className="text-[11px] text-muted-foreground mt-1 max-w-2xl">
                            {t("consortiums.intro")}
                        </p>
                    </div>
                    {!mine && (
                        <button
                            type="button"
                            onClick={() => setShowCreate((x) => !x)}
                            data-testid="consortiums-create-toggle"
                            className="text-[10px] tracking-widest px-3 py-1.5 border border-amber text-amber rounded-sm hover:bg-amber/10"
                        >
                            {showCreate ? t("consortiums.cancel") : t("consortiums.create")}
                        </button>
                    )}
                </header>

                {showCreate && !mine && (
                    <form
                        onSubmit={onCreate}
                        data-testid="consortiums-create-form"
                        className="mb-6 border border-border/60 bg-card/40 rounded-sm p-4 space-y-3"
                    >
                        <div>
                            <label className="block text-[10px] text-muted-foreground tracking-widest mb-1">
                                {t("consortiums.field_name")}
                            </label>
                            <input
                                value={form.name}
                                onChange={(e) => setForm({ ...form, name: e.target.value })}
                                maxLength={40}
                                minLength={3}
                                required
                                data-testid="consortiums-input-name"
                                className="w-full bg-background border border-border/60 px-2 py-1 text-[12px] rounded-sm focus:border-amber outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] text-muted-foreground tracking-widest mb-1">
                                {t("consortiums.field_tag")} ({t("consortiums.optional")})
                            </label>
                            <input
                                value={form.tag}
                                onChange={(e) => setForm({ ...form, tag: e.target.value })}
                                maxLength={6}
                                data-testid="consortiums-input-tag"
                                className="w-full bg-background border border-border/60 px-2 py-1 text-[12px] rounded-sm focus:border-amber outline-none uppercase"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] text-muted-foreground tracking-widest mb-1">
                                {t("consortiums.field_description")}
                            </label>
                            <textarea
                                value={form.description}
                                onChange={(e) => setForm({ ...form, description: e.target.value })}
                                maxLength={300}
                                rows={2}
                                data-testid="consortiums-input-description"
                                className="w-full bg-background border border-border/60 px-2 py-1 text-[12px] rounded-sm focus:border-amber outline-none"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={busy === "create"}
                            data-testid="consortiums-create-submit"
                            className="text-[10px] tracking-widest px-3 py-1.5 border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-50"
                        >
                            {busy === "create" ? "…" : t("consortiums.create_submit")}
                        </button>
                    </form>
                )}

                {loading ? (
                    <div data-testid="consortiums-loading" className="text-[11px] text-muted-foreground">
                        :: {t("consortiums.loading")}
                    </div>
                ) : mine ? (
                    <div
                        data-testid="consortiums-mine"
                        className="border border-amber/60 bg-card/40 rounded-sm p-4 mb-6"
                    >
                        <div className="flex items-baseline justify-between mb-2 gap-2">
                            <h2 className="text-amber tracking-widest text-[11px]">
                                :: {t("consortiums.you_are_in")}
                            </h2>
                            <button
                                type="button"
                                onClick={onLeave}
                                disabled={busy === "leave"}
                                data-testid="consortiums-leave"
                                className="text-[10px] tracking-widest px-2 py-1 border border-border/60 text-muted-foreground hover:text-red-400 hover:border-red-400 rounded-sm disabled:opacity-50"
                            >
                                {busy === "leave" ? "…" : t("consortiums.leave")}
                            </button>
                        </div>
                        <div className="text-foreground text-base mb-1" data-testid={`consortium-name-${mine.id}`}>
                            {mine.name}{mine.tag ? <span className="text-amber/70 ml-2 text-[11px]">[{mine.tag}]</span> : null}
                        </div>
                        {mine.description && (
                            <p className="text-[11px] text-muted-foreground mb-3">{mine.description}</p>
                        )}
                        <div className="text-[10px] text-muted-foreground tracking-widest mb-2">
                            {t("consortiums.members")} ({mine.member_count})
                        </div>
                        <ul className="space-y-1">
                            {(mine.members || []).map((m) => (
                                <li
                                    key={m.id}
                                    data-testid={`consortium-member-${m.id}`}
                                    className="text-[11px] flex justify-between border-l-2 border-border/40 pl-3"
                                >
                                    <span className="text-foreground/90">{m.guild_name}</span>
                                    <span className="text-muted-foreground tracking-widest">{m.role}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ) : null}

                <div
                    data-testid="consortiums-list"
                    className="border border-border/60 bg-card/40 rounded-sm p-4"
                >
                    <div className="text-amber tracking-widest text-[11px] mb-3">
                        :: {t("consortiums.list_title")}
                    </div>
                    {list.length === 0 ? (
                        <div className="text-[11px] text-muted-foreground italic">
                            :: {t("consortiums.empty")}
                        </div>
                    ) : (
                        <ul className="space-y-2">
                            {list.map((c) => (
                                <li
                                    key={c.id}
                                    data-testid={`consortium-row-${c.id}`}
                                    className="border-l-2 border-border/40 pl-3 flex items-baseline justify-between gap-3 flex-wrap"
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="text-foreground/90 truncate">
                                            {c.name}
                                            {c.tag ? <span className="text-amber/70 ml-2 text-[10px]">[{c.tag}]</span> : null}
                                        </div>
                                        <div className="text-[10px] text-muted-foreground">
                                            {c.member_count} {t("consortiums.members_label")}
                                            {c.description ? ` · ${c.description.slice(0, 80)}` : ""}
                                        </div>
                                    </div>
                                    {!mine && (
                                        <button
                                            type="button"
                                            onClick={() => onJoin(c.id)}
                                            disabled={busy === `join-${c.id}`}
                                            data-testid={`consortium-join-${c.id}`}
                                            className="shrink-0 text-[10px] tracking-widest px-2 py-1 border border-amber text-amber rounded-sm hover:bg-amber/10 disabled:opacity-50"
                                        >
                                            {busy === `join-${c.id}` ? "…" : t("consortiums.join")}
                                        </button>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </main>
        </div>
    );
}
