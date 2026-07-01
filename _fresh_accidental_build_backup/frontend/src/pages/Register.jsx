import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { errorMessage } from "@/lib/api";

export default function Register() {
    const nav = useNavigate();
    const { register } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const onSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        if (password.length < 8) {
            setError("La password deve avere almeno 8 caratteri.");
            return;
        }
        setLoading(true);
        try {
            await register(email, password);
            toast.success("Account creato. Ora fonda la tua gilda.");
            nav("/create-guild", { replace: true });
        } catch (err) {
            const msg = errorMessage(err, "Registrazione fallita.");
            setError(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-scanline">
            <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-10">
                <p className="mb-6 text-xs uppercase tracking-widest text-muted-foreground">
                    <Link to="/" className="hover:text-amber">&larr; back</Link>
                </p>
                <h1 className="mb-2 text-3xl font-semibold tracking-tight">
                    Registrati<span className="text-amber">.</span>
                </h1>
                <p className="mb-8 text-sm text-muted-foreground">
                    Un solo account, una sola gilda.
                </p>
                <Card className="border-border/70 bg-card p-6">
                    <form onSubmit={onSubmit} className="space-y-4" data-testid="register-form">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-xs uppercase tracking-widest text-muted-foreground">
                                Email
                            </Label>
                            <Input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                autoComplete="email"
                                placeholder="tu@example.com"
                                data-testid="register-email-input"
                                className="border-border/70 bg-background"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-xs uppercase tracking-widest text-muted-foreground">
                                Password <span className="text-muted-foreground/70">(min 8)</span>
                            </Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={8}
                                autoComplete="new-password"
                                data-testid="register-password-input"
                                className="border-border/70 bg-background"
                            />
                        </div>
                        {error && (
                            <div
                                role="alert"
                                data-testid="register-error"
                                className="rounded-sm border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive"
                            >
                                {error}
                            </div>
                        )}
                        <Button
                            type="submit"
                            disabled={loading}
                            data-testid="register-submit-btn"
                            className="w-full bg-amber text-black hover:bg-amber/90"
                        >
                            {loading ? "Creazione in corso…" : "Crea account"}
                        </Button>
                    </form>
                </Card>
                <p className="mt-6 text-center text-xs text-muted-foreground">
                    Hai già un account?{" "}
                    <Link to="/login" className="text-amber hover:underline" data-testid="register-goto-login">
                        Accedi
                    </Link>
                </p>
            </div>
        </div>
    );
}
