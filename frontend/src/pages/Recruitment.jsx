import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import AppHeader from "../components/AppHeader";
import OverCapBanner from "../components/OverCapBanner";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";
import { api, formatApiError } from "../lib/api";

const EMPTY_FORM = { name: "", race_slug: "", gender: "" };

export default function Recruitment() {
    const { guild, refreshGuild } = useAuth();
    const [options, setOptions] = useState(null);
    const [form, setForm] = useState(EMPTY_FORM);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);

    const load = async () => {
        try {
            const { data } = await api.get("/recruitment/model");
            setOptions(data);
            setForm((old) => ({
                ...old,
                race_slug: old.race_slug || data.races?.[0]?.slug || "",
                gender: old.gender || data.genders?.[0]?.id || "",
            }));
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const full = Boolean(
        options && options.active_roster >= options.roster_cap,
    );
    const canAfford = (guild?.gold ?? 0) >= (options?.cost_gold ?? 0);
    const valid = useMemo(
        () => form.name.trim().length >= 2 && form.race_slug && form.gender,
        [form],
    );

    const createModel = async (event) => {
        event.preventDefault();
        if (!valid || full || !canAfford || busy) return;
        setBusy(true);
        try {
            const { data } = await api.post("/recruitment/model", {
                ...form,
                name: form.name.trim(),
            });
            toast.success(`${data.adventurer.name} si è unito alla gilda.`);
            setForm((old) => ({ ...old, name: "" }));
            await Promise.all([load(), refreshGuild()]);
        } catch (err) {
            toast.error(formatApiError(err));
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader />
            <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6" data-testid="recruitment-page">
                <OverCapBanner source="recruitment" />
                <h1 className="text-xs tracking-[0.3em] text-amber mb-3">
                    :: CREA UN NUOVO AVVENTURIERO
                </h1>
                <p className="text-sm text-muted-foreground max-w-3xl mb-6">
                    Qui non si estraggono candidati casuali: costruisci un modello base scegliendone
                    identità, razza e genere. Nascerà al livello 1, di rarità Comune e senza classe;
                    la sua prima vera scelta sarà entrare in una Class Hall.
                </p>

                {loading || !options ? (
                    <div className="text-xs text-muted-foreground">Caricamento…</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-[1fr_280px] gap-5">
                        <form
                            onSubmit={createModel}
                            className="border border-border bg-card rounded-sm p-5 space-y-4"
                            data-testid="base-model-form"
                        >
                            <label className="block">
                                <span className="block text-[10px] tracking-widest text-muted-foreground mb-1.5">
                                    NOME
                                </span>
                                <input
                                    value={form.name}
                                    maxLength={40}
                                    onChange={(e) => setForm((old) => ({ ...old, name: e.target.value }))}
                                    className="w-full bg-secondary border border-border px-3 py-2 text-sm outline-none focus:border-amber"
                                    placeholder="Scegli un nome"
                                    data-testid="base-model-name"
                                />
                            </label>

                            <label className="block">
                                <span className="block text-[10px] tracking-widest text-muted-foreground mb-1.5">
                                    RAZZA
                                </span>
                                <select
                                    value={form.race_slug}
                                    onChange={(e) => setForm((old) => ({ ...old, race_slug: e.target.value }))}
                                    className="w-full bg-secondary border border-border px-3 py-2 text-sm outline-none focus:border-amber"
                                    data-testid="base-model-race"
                                >
                                    {(options.races || []).map((race) => (
                                        <option key={race.slug} value={race.slug}>
                                            {race.name_it || race.name_en || race.slug}
                                        </option>
                                    ))}
                                </select>
                            </label>

                            <fieldset>
                                <legend className="text-[10px] tracking-widest text-muted-foreground mb-2">
                                    GENERE
                                </legend>
                                <div className="grid grid-cols-2 gap-2">
                                    {(options.genders || []).map((gender) => (
                                        <button
                                            key={gender.id}
                                            type="button"
                                            onClick={() => setForm((old) => ({ ...old, gender: gender.id }))}
                                            className={`border px-3 py-2 text-xs ${
                                                form.gender === gender.id
                                                    ? "border-amber text-amber bg-amber/10"
                                                    : "border-border text-muted-foreground"
                                            }`}
                                        >
                                            {gender.name_it}
                                        </button>
                                    ))}
                                </div>
                            </fieldset>

                            {full && (
                                <p className="text-xs text-amber">
                                    Dormitori pieni: potenzia la struttura o congeda un avventuriero.
                                </p>
                            )}
                            {!full && !canAfford && (
                                <p className="text-xs text-amber">
                                    Oro insufficiente: servono {options.cost_gold} monete.
                                </p>
                            )}

                            <Button
                                type="submit"
                                disabled={!valid || full || !canAfford || busy}
                                className="w-full rounded-sm"
                                data-testid="create-base-model"
                            >
                                {busy
                                    ? "Creazione…"
                                    : options.cost_gold === 0
                                        ? "Crea gratuitamente"
                                        : `Crea per ${options.cost_gold} oro`}
                            </Button>
                        </form>

                        <aside className="border border-amber/30 bg-amber/5 rounded-sm p-4 h-fit">
                            <div className="text-[10px] tracking-widest text-amber mb-3">
                                MODELLO BASE
                            </div>
                            <dl className="space-y-2 text-xs">
                                <div className="flex justify-between gap-3">
                                    <dt className="text-muted-foreground">Rarità</dt>
                                    <dd>Comune</dd>
                                </div>
                                <div className="flex justify-between gap-3">
                                    <dt className="text-muted-foreground">Livello</dt>
                                    <dd>1</dd>
                                </div>
                                <div className="flex justify-between gap-3">
                                    <dt className="text-muted-foreground">Classe</dt>
                                    <dd>Senza classe</dd>
                                </div>
                                <div className="flex justify-between gap-3">
                                    <dt className="text-muted-foreground">Statistiche</dt>
                                    <dd>5 ciascuna</dd>
                                </div>
                                <div className="flex justify-between gap-3 border-t border-border pt-2">
                                    <dt className="text-muted-foreground">Avventurieri</dt>
                                    <dd>{options.active_roster}/{options.roster_cap}</dd>
                                </div>
                            </dl>
                            <p className="text-[11px] text-muted-foreground mt-4">
                                I primi {options.free_founders} fondatori sono gratuiti. Dopo di loro
                                il costo cresce progressivamente con la dimensione della compagnia.
                            </p>
                            <Link to="/class-halls" className="block text-xs text-amber hover:underline mt-4">
                                Esplora le Class Hall →
                            </Link>
                        </aside>
                    </div>
                )}
            </main>
        </div>
    );
}
