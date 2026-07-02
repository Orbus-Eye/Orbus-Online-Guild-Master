import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "./ui/alert-dialog";
import { api } from "../lib/api";

/** ROUND 16.5.1 B.3 UI — Card "Ultimo raid completato" con replay preview.
 *
 * Comportamento:
 * - Su mount: GET /api/raids/last → renderizza card (o empty state)
 * - Bottone "Ripeti raid": POST /api/raids/replay-preview → modal conferma
 * - Nessun auto-start: sempre richiede conferma esplicita
 */
export default function LastRaidCard() {
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, raid: null,
                                        participants: [], error: null });
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true }));
    try {
      const r = await api.get("/api/raids/last");
      setState({ loading: false, raid: r.data.raid,
                 participants: r.data.participants || [], error: null });
    } catch (e) {
      const status = e.response?.status;
      const detail = e.response?.data?.detail || e.message;
      if (status === 404) {
        setState({ loading: false, raid: null, participants: [],
                   error: null });
      } else {
        setState({ loading: false, raid: null, participants: [],
                   error: detail });
      }
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openReplayPreview = async () => {
    if (!state.raid) return;
    setPreviewLoading(true);
    try {
      const squadIds = state.participants.map((p) => p.adventurer_id);
      const r = await api.post("/api/raids/replay-preview", {
        raid_slug: state.raid.raid_dungeon_slug,
        squad_ids: squadIds,
      });
      setPreview({ ...r.data, squad_ids: squadIds });
    } catch (e) {
      toast.error(`Errore anteprima replay: ${e.response?.data?.detail || e.message}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  const confirmReplay = () => {
    // Non avvia in automatico: reindirizza a RaidBuilder con preselezioni
    // via query string. L'utente conferma manualmente da lì.
    const slug = state.raid.raid_dungeon_slug;
    const ids = preview.squad_ids.join(",");
    setPreview(null);
    navigate(`/raid-builder?raid_slug=${encodeURIComponent(slug)}&squad_ids=${encodeURIComponent(ids)}`);
  };

  // Loading state
  if (state.loading) {
    return (
      <Card className="bg-slate-800 border-slate-700"
            data-testid="last-raid-card-loading">
        <CardContent className="py-6 text-slate-400">
          Caricamento ultimo raid…
        </CardContent>
      </Card>
    );
  }
  // Empty state
  if (!state.raid) {
    return (
      <Card className="bg-slate-800 border-slate-700"
            data-testid="last-raid-card-empty">
        <CardHeader><CardTitle>Ultimo Raid</CardTitle></CardHeader>
        <CardContent className="text-slate-400 text-sm">
          Nessun raid ancora completato. Vai su Raid per iniziarne uno.
        </CardContent>
      </Card>
    );
  }

  const r = state.raid;
  const outcomeColor = r.outcome === "success" ? "text-emerald-400"
                       : r.outcome === "failure" ? "text-rose-400"
                       : "text-slate-300";
  const outcomeLabel = r.outcome === "success" ? "Vittoria"
                       : r.outcome === "failure" ? "Sconfitta"
                       : (r.outcome || "—");

  return (
    <>
      <Card className="bg-slate-800 border-slate-700"
            data-testid="last-raid-card">
        <CardHeader className="pb-2">
          <CardTitle className="flex flex-wrap items-center gap-2">
            <span>Ultimo Raid</span>
            <span className="text-xs font-mono text-slate-500 truncate">
              {r.raid_dungeon_slug}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Esito"
                  value={outcomeLabel}
                  className={outcomeColor}
                  testid="last-raid-outcome" />
            <Stat label="Score"
                  value={r.raid_score ?? "—"}
                  testid="last-raid-score" />
            <Stat label="Durata"
                  value={r.duration_seconds
                    ? `${Math.round(r.duration_seconds / 60)}m`
                    : "—"}
                  testid="last-raid-duration" />
            <Stat label="Squadra"
                  value={`${state.participants.length} avv`}
                  testid="last-raid-squad-count" />
          </div>
          {r.rewards && (
            <div className="border border-slate-700 rounded p-2 text-xs text-slate-300"
                 data-testid="last-raid-rewards">
              <span className="text-slate-500 uppercase mr-2">Ricompense:</span>
              {r.rewards.gold ? <span className="mr-3">Oro {r.rewards.gold}</span> : null}
              {r.rewards.xp ? <span className="mr-3">XP {r.rewards.xp}</span> : null}
              {r.rewards.items?.length
                ? <span>Item {r.rewards.items.length}</span>
                : null}
            </div>
          )}
          <Button onClick={openReplayPreview}
                  disabled={previewLoading}
                  className="w-full md:w-auto"
                  data-testid="last-raid-replay-btn">
            {previewLoading ? "Verifica…" : "Ripeti raid"}
          </Button>
        </CardContent>
      </Card>

      {/* Preview modal */}
      <AlertDialog open={!!preview} onOpenChange={(o) => !o && setPreview(null)}>
        <AlertDialogContent data-testid="replay-preview-modal">
          <AlertDialogHeader>
            <AlertDialogTitle>Ripeti raid — Anteprima</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2 text-sm">
                {preview && (
                  <>
                    <div>
                      Raid: <span className="font-mono">{r.raid_dungeon_slug}</span>{" "}
                      {preview.raid_available ? (
                        <span className="text-emerald-400"
                              data-testid="replay-raid-available">disponibile</span>
                      ) : (
                        <span className="text-rose-400"
                              data-testid="replay-raid-unavailable">non più disponibile</span>
                      )}
                    </div>
                    <div>
                      Squadra: {state.participants.length} avventurieri
                    </div>
                    {preview.unavailable_adventurers?.length > 0 && (
                      <div className="text-amber-400"
                           data-testid="replay-unavailable-warnings">
                        Avv non disponibili:
                        <ul className="list-disc list-inside">
                          {preview.unavailable_adventurers.map((a) => (
                            <li key={a.id}>
                              {a.name} — {a.reasons.join(", ")}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {preview.missing_adventurers?.length > 0 && (
                      <div className="text-rose-400"
                           data-testid="replay-missing-warnings">
                        Avv mancanti: {preview.missing_adventurers.length}
                      </div>
                    )}
                    {preview.raid_available
                      && preview.all_adventurers_available
                      && preview.all_adventurers_owned && (
                      <div className="text-emerald-400"
                           data-testid="replay-ready">
                        Tutto pronto per il replay.
                      </div>
                    )}
                  </>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="replay-cancel">
              Annulla
            </AlertDialogCancel>
            <AlertDialogAction onClick={confirmReplay}
                               disabled={!preview?.raid_available}
                               data-testid="replay-confirm">
              Vai al Raid Builder
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function Stat({ label, value, className = "", testid }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded p-2"
         data-testid={testid}>
      <div className="text-xs text-slate-500 uppercase">{label}</div>
      <div className={`font-mono text-sm ${className}`}>{value}</div>
    </div>
  );
}
