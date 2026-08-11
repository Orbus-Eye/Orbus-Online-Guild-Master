import { useEffect, useMemo, useState } from "react";
import { api, formatApiError } from "../lib/api";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";

const STATUS_LABEL = {
  equipped: "Equipaggiato",
  owned: "Posseduto",
  undiscovered: "Da trovare",
};

export default function ClassHallCollectionBook() {
  const [book, setBook] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [wave, setWave] = useState("ALL");
  const [openHall, setOpenHall] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/class-halls/collection-book");
      setBook(response.data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const halls = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase("it");
    return (book?.halls || []).filter((hall) => {
      if (wave !== "ALL" && hall.wave !== wave) return false;
      if (!needle) return true;
      return [
        hall.class_name_it,
        hall.hall_name_it,
        hall.hall_master_witness_npc,
        hall.lore_hook_it,
        ...hall.items.map((entry) => entry.item.display_name_it),
      ].some((value) => String(value || "").toLocaleLowerCase("it").includes(needle));
    });
  }, [book, query, wave]);

  return (
    <Card className="bg-slate-900/70 border-amber-700/40"
          data-testid="class-hall-collection-book">
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Libro degli Oggetti delle Class Hall</CardTitle>
            <p className="text-sm text-slate-400 mt-1">
              Centotrentacinque oggetti singolari: cinque memorie, strumenti
              o reliquie per ognuna delle ventisette vie.
            </p>
          </div>
          <Button variant="outline" onClick={load} disabled={loading}>
            {loading ? "Aggiornamento…" : "Aggiorna collezione"}
          </Button>
        </div>
        {book && (
          <div className="grid gap-3 md:grid-cols-3">
            <Metric label="Oggetti scoperti"
                    value={`${book.owned_count}/${book.total_count}`} />
            <Metric label="Completamento"
                    value={`${book.completion_percent}%`} />
            <Metric label="Sentieri completi"
                    value={`${book.completed_halls}/${book.total_halls}`} />
          </div>
        )}
        <div className="flex flex-col gap-2 md:flex-row">
          <Input value={query}
                 onChange={(event) => setQuery(event.target.value)}
                 placeholder="Cerca classe, Hall, Maestro, lore o oggetto…"
                 className="bg-slate-950 border-slate-700" />
          <div className="flex flex-wrap gap-1">
            {["ALL", "A", "B", "C", "D", "E"].map((value) => (
              <Button key={value}
                      size="sm"
                      variant={wave === value ? "default" : "outline"}
                      onClick={() => setWave(value)}>
                {value === "ALL" ? "Tutte" : `Wave ${value}`}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="rounded border border-rose-700 bg-rose-950/40 p-3 text-sm text-rose-200">
            {error}
          </div>
        )}
        {!loading && !error && halls.length === 0 && (
          <div className="text-sm text-slate-400">Nessun sentiero corrisponde ai filtri.</div>
        )}
        <div className="grid gap-3">
          {halls.map((hall) => {
            const expanded = openHall === hall.hall_id;
            return (
              <div key={hall.hall_id}
                   className="rounded-lg border border-slate-700 bg-slate-950/70">
                <button type="button"
                        className="w-full p-4 text-left"
                        onClick={() => setOpenHall(expanded ? null : hall.hall_id)}
                        aria-expanded={expanded}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-wide text-amber-400">
                        Wave {hall.wave} · {hall.class_name_it}
                      </div>
                      <div className="font-semibold text-slate-100">{hall.hall_name_it}</div>
                      <div className="text-xs text-slate-500">
                        {hall.hall_master_witness_npc} · {hall.assigned_adventurers} avventurieri
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={hall.is_complete ? "text-emerald-300" : "text-slate-200"}>
                        {hall.owned_count}/{hall.total_count}
                      </div>
                      <div className="text-xs text-slate-500">
                        {hall.equipped_count} equipaggiati
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded bg-slate-800">
                    <div className="h-full bg-amber-500 transition-all"
                         style={{ width: `${hall.owned_count / hall.total_count * 100}%` }} />
                  </div>
                </button>
                {expanded && (
                  <div className="border-t border-slate-800 p-4 space-y-3">
                    <p className="text-sm italic text-slate-400">“{hall.lore_hook_it}”</p>
                    {hall.items.map((entry) => (
                      <div key={entry.item.id}
                           className={`rounded border p-3 ${
                             entry.status === "equipped"
                               ? "border-emerald-700 bg-emerald-950/20"
                               : entry.status === "owned"
                                 ? "border-amber-700 bg-amber-950/20"
                                 : "border-slate-800 bg-slate-900/50"
                           }`}>
                        <div className="flex flex-wrap justify-between gap-2">
                          <div>
                            <div className="font-medium">
                              {entry.order + 1}. {entry.item.display_name_it}
                              {entry.is_signature ? " · Item-firma" : ""}
                            </div>
                            <div className="text-xs text-slate-500">
                              {entry.item.rarity} · {entry.item.item_type}
                              {entry.item.has_runtime_effect ? " · effetto distintivo" : ""}
                            </div>
                          </div>
                          <span className="text-xs rounded-full border border-slate-700 px-2 py-1">
                            {STATUS_LABEL[entry.status]}
                            {entry.owned_quantity > 1 ? ` ×${entry.owned_quantity}` : ""}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-slate-300">
                          {entry.item.flavor_text_it || entry.item.description_it}
                        </p>
                        <p className="mt-1 text-xs text-amber-300/80">
                          Provenienza: {entry.item.acquisition_hint_it}
                        </p>
                        {entry.item.effect_summary_it && (
                          <p className="mt-1 text-xs text-cyan-300/80">
                            Effetto: {entry.item.effect_summary_it}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded border border-slate-700 bg-slate-950 p-3">
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className="text-xl font-semibold text-amber-300">{value}</div>
    </div>
  );
}
