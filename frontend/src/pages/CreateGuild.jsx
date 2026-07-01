import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { errorMessage } from "@/lib/api";

export default function CreateGuild() {
    const nav = useNavigate();
    const { createGuild, logout } = useAuth();
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const onSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        if (name.trim().length < 3) {
            setError("Il nome della gilda deve avere almeno 3 caratteri.");
            return;
        }
        setLoading(true);
        try {
            await createGuild(name.trim(), description.trim());
            toast.success("Gilda fondata!");
            nav("/dashboard", { replace: true });
        } catch (err) {
            const msg = errorMessage(err, "Creazione gilda fallita.");
            setError(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    const onLogout = () => {
        logout();
        nav("/", { replace: true });
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-scanline">
            <div className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6 py-10">
                <div className="mb-4 flex items-center justify-between">
                    <p className="text-xs uppercase tracking-widest text-muted-foreground">
                        &gt; onboarding · step 1/1
                    </p>
                    <button
                        type="button"
                        onClick={onLogout}
                        data-testid="create-guild-logout-btn"
                        className="text-xs text-muted-foreground hover:text-amber"
                    >
                        Logout
                    </button>
                </div>

                <h1 className="mb-2 text-3xl font-semibold tracking-tight">
                    Fonda la tua gilda<span className="text-amber">.</span>
                </h1>
                <p className="mb-8 text-sm text-muted-foreground">
                    Un solo tentativo. Scegli con cura: il nome ti rappresenterà
                    davanti alle altre gilde di Orbus.
                </p>

                <Card className="border-border/70 bg-card p-6">
                    <form onSubmit={onSubmit} className="space-y-4" data-testid="create-guild-form">
                        <div className="space-y-2">
                            <Label htmlFor="name" className="text-xs uppercase tracking-widest text-muted-foreground">
                                Nome gilda <span className="text-muted-foreground/70">(3–40 caratteri)</span>
                            </Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                minLength={3}
                                maxLength={40}
                                placeholder="Es. Ordo Aurorae"
                                data-testid="create-guild-name-input"
                                className="border-border/70 bg-background"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description" className="text-xs uppercase tracking-widest text-muted-foreground">
                                Descrizione <span className="text-muted-foreground/70">(max 500)</span>
                            </Label>
                            <Textarea
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                maxLength={500}
                                rows={4}
                                placeholder="Cosa contraddistingue la tua gilda?"
                                data-testid="create-guild-description-input"
                                className="border-border/70 bg-background"
                            />
                            <p className="text-right text-[10px] text-muted-foreground">
                                {description.length}/500
                            </p>
                        </div>
                        {error && (
                            <div
                                role="alert"
                                data-testid="create-guild-error"
                                className="rounded-sm border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive"
                            >
                                {error}
                            </div>
                        )}
                        <Button
                            type="submit"
                            disabled={loading}
                            data-testid="create-guild-submit-btn"
                            className="w-full bg-amber text-black hover:bg-amber/90"
                        >
                            {loading ? "Fondazione in corso…" : "Fonda la gilda"}
                        </Button>
                    </form>
                </Card>
            </div>
        </div>
    );
}
