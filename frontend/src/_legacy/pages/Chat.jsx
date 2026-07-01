import { useEffect, useRef, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { toast } from "sonner";
import AppHeader from "../components/AppHeader";
import { Button } from "../components/ui/button";

/**
 * Phase 19.3 — Chat MVP.
 *
 * Two tabs (Globale | Consorzio). Polling every 7s.
 * Hard rule: NEVER render `message_text` via dangerouslySetInnerHTML. The
 * backend already HTML-escapes; we render as plain text, which gives us a
 * second layer of defense against XSS regression.
 */

const POLL_INTERVAL_MS = 7000;
const MAX_TEXT = 500;

function relativeTime(iso) {
    if (!iso) return "";
    const then = new Date(iso).getTime();
    const diff = Math.round((Date.now() - then) / 1000);
    if (diff < 5) return "ora";
    if (diff < 60) return `${diff}s fa`;
    const m = Math.floor(diff / 60);
    if (m < 60) return `${m} min fa`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h fa`;
    const d = Math.floor(h / 24);
    return `${d}g fa`;
}

const MessageRow = ({ msg }) => (
    <div
        data-testid={`chat-msg-${msg.message_id}`}
        className="border-b border-border/40 py-2 px-1"
    >
        <div className="flex items-baseline gap-2">
            <span className="text-amber text-xs tracking-wider font-medium">
                {msg.sender_public_name || "Anonymous Guild"}
            </span>
            <span className="text-[10px] text-muted-foreground">
                {relativeTime(msg.created_at)}
            </span>
        </div>
        {/* Plain-text render; backend already escaped <,>,&,",' → entities */}
        <div className="text-sm text-foreground whitespace-pre-wrap break-words">
            {msg.message_text}
        </div>
    </div>
);

export default function Chat() {
    const [tab, setTab] = useState("global"); // "global" | "consortium"
    const [consortium, setConsortium] = useState(null); // {id, name} or null
    const [consortiumLoading, setConsortiumLoading] = useState(true);
    const [messages, setMessages] = useState([]);
    const [draft, setDraft] = useState("");
    const [sending, setSending] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const scrollRef = useRef(null);
    const lastTsRef = useRef(null);

    // Resolve current user's consortium membership (for tab visibility)
    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get("/consortiums/me");
                setConsortium(data.consortium || null);
            } catch {
                setConsortium(null);
            } finally {
                setConsortiumLoading(false);
            }
        })();
    }, []);

    const fetchMessages = useCallback(
        async (incremental = false) => {
            setError(null);
            try {
                const params = new URLSearchParams();
                params.set("limit", "100");
                if (incremental && lastTsRef.current) {
                    params.set("after", lastTsRef.current);
                }
                let url;
                if (tab === "global") {
                    url = `/chat/global?${params.toString()}`;
                } else if (consortium?.id) {
                    url = `/chat/consortium/${consortium.id}?${params.toString()}`;
                } else {
                    setMessages([]);
                    setLoading(false);
                    return;
                }
                const { data } = await api.get(url);
                const fresh = data.messages || [];
                if (incremental && fresh.length === 0) {
                    return;
                }
                setMessages((prev) => {
                    if (!incremental) return fresh;
                    const seen = new Set(prev.map((m) => m.message_id));
                    const merged = [
                        ...prev,
                        ...fresh.filter((m) => !seen.has(m.message_id)),
                    ];
                    return merged.slice(-200);
                });
                if (fresh.length > 0) {
                    lastTsRef.current = fresh[fresh.length - 1].created_at;
                }
            } catch (err) {
                if (err?.response?.status === 401) {
                    setError("Sessione scaduta. Effettua di nuovo il login.");
                } else if (err?.response?.status === 403) {
                    setError("Accesso non consentito a questa chat.");
                } else {
                    setError("Errore di rete. Riprovo automaticamente…");
                }
            } finally {
                setLoading(false);
            }
        },
        [tab, consortium],
    );

    // Initial load + tab change reset
    useEffect(() => {
        setLoading(true);
        setMessages([]);
        lastTsRef.current = null;
        fetchMessages(false);
    }, [fetchMessages]);

    // Polling
    useEffect(() => {
        const id = setInterval(() => fetchMessages(true), POLL_INTERVAL_MS);
        return () => clearInterval(id);
    }, [fetchMessages]);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    async function send() {
        const text = draft.trim();
        if (!text || sending) return;
        setSending(true);
        try {
            const url =
                tab === "global"
                    ? "/chat/global"
                    : `/chat/consortium/${consortium.id}`;
            await api.post(url, { message_text: text });
            setDraft("");
            await fetchMessages(true);
        } catch (err) {
            const status = err?.response?.status;
            if (status === 429) {
                toast.error("Rallenta un attimo. Massimo 5 messaggi ogni 10 secondi.");
            } else if (status === 422) {
                toast.error("Messaggio non valido (vuoto o troppo lungo).");
            } else if (status === 403) {
                toast.error("Non hai accesso a questa chat.");
            } else {
                toast.error(formatApiError(err));
            }
        } finally {
            setSending(false);
        }
    }

    const inConsortium = !!consortium?.id;
    const showEmptyConsortium = tab === "consortium" && !consortiumLoading && !inConsortium;

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg">
            <AppHeader subtitleKey="nav.chat" />
            <main className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
                <div className="text-xs text-amber tracking-widest mb-2">:: CHAT</div>
                <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight mb-1">
                    Chat
                </h1>
                <p className="text-xs text-muted-foreground mb-5 max-w-xl">
                    Comunica con altre gilde. Niente dati personali. Polling ogni 7s.
                    Vedi la sezione <Link to="/guide" className="underline">Guida</Link> per le regole complete.
                </p>

                {/* Tabs */}
                <div className="flex gap-1 mb-4 border-b border-border/60">
                    <button
                        type="button"
                        data-testid="chat-tab-global"
                        onClick={() => setTab("global")}
                        className={
                            "px-3 py-2 text-xs tracking-widest border-b-2 transition-colors " +
                            (tab === "global"
                                ? "border-amber text-amber"
                                : "border-transparent text-muted-foreground hover:text-foreground")
                        }
                    >
                        GLOBALE
                    </button>
                    <button
                        type="button"
                        data-testid="chat-tab-consortium"
                        onClick={() => setTab("consortium")}
                        className={
                            "px-3 py-2 text-xs tracking-widest border-b-2 transition-colors " +
                            (tab === "consortium"
                                ? "border-amber text-amber"
                                : "border-transparent text-muted-foreground hover:text-foreground")
                        }
                    >
                        CONSORZIO{inConsortium ? ` · ${consortium.name}` : ""}
                    </button>
                </div>

                {/* Empty state: consortium tab without membership */}
                {showEmptyConsortium && (
                    <div
                        data-testid="chat-consortium-empty"
                        className="border border-border bg-card rounded-sm p-6 text-center text-sm text-muted-foreground"
                    >
                        <p className="mb-3">Entra in un Consorzio per usare questa chat.</p>
                        <Link to="/consortiums">
                            <Button
                                data-testid="chat-goto-consortiums"
                                className="h-8 px-3 text-xs bg-amber text-black hover:bg-amber/80 rounded-sm"
                            >
                                ▶ Vai ai Consorzi
                            </Button>
                        </Link>
                    </div>
                )}

                {!showEmptyConsortium && (
                    <>
                        <div
                            ref={scrollRef}
                            data-testid="chat-messages"
                            className="border border-border bg-card rounded-sm h-[55vh] sm:h-[60vh] overflow-y-auto px-3"
                        >
                            {loading && (
                                <div className="py-4 text-xs text-muted-foreground">
                                    Caricamento…
                                </div>
                            )}
                            {!loading && messages.length === 0 && (
                                <div
                                    data-testid="chat-empty"
                                    className="py-6 text-xs text-muted-foreground text-center"
                                >
                                    Nessun messaggio ancora. Apri tu la conversazione.
                                </div>
                            )}
                            {messages.map((m) => (
                                <MessageRow key={m.message_id} msg={m} />
                            ))}
                        </div>

                        {error && (
                            <div
                                data-testid="chat-error"
                                className="mt-2 text-[11px] text-destructive"
                            >
                                {error}
                            </div>
                        )}

                        {/* Composer */}
                        <div className="mt-3 flex gap-2 items-end">
                            <textarea
                                data-testid="chat-input"
                                value={draft}
                                onChange={(e) => setDraft(e.target.value.slice(0, MAX_TEXT))}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        send();
                                    }
                                }}
                                placeholder="Scrivi un messaggio… (Invio per inviare)"
                                rows={2}
                                maxLength={MAX_TEXT}
                                className="flex-1 bg-card border border-border rounded-sm px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-amber resize-none"
                            />
                            <div className="flex flex-col items-end gap-1">
                                <Button
                                    type="button"
                                    data-testid="chat-send-btn"
                                    onClick={send}
                                    disabled={sending || !draft.trim()}
                                    className="h-9 px-4 text-xs bg-amber text-black hover:bg-amber/80 disabled:opacity-50 rounded-sm"
                                >
                                    {sending ? "…" : "Invia"}
                                </Button>
                                <span className="text-[10px] text-muted-foreground">
                                    {draft.length}/{MAX_TEXT}
                                </span>
                            </div>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
