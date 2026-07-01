import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { errorMessage } from "@/lib/api";

export default function Login() {
    const nav = useNavigate();
    const { login } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const onSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            await login(email, password);
            toast.success("Accesso effettuato.");
            // La destinazione verrà gestita da RouteGuards; forziamo /dashboard
            nav("/dashboard", { replace: true });
        } catch (err) {
            const msg = errorMessage(err, "Credenziali non valide.");
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
                    Accedi<span className="text-amber">.</span>
                </h1>
                <p className="mb-8 text-sm text-muted-foreground">
                    Entra nel tuo terminale gilda.
                </p>
                <Card className="border-border/70 bg-card p-6">
                    <form onSubmit={onSubmit} className="space-y-4" data-testid="login-form">
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
                                autoComplete="username"
                                placeholder="tu@example.com"
                                data-testid="login-email-input"
                                className="border-border/70 bg-background"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-xs uppercase tracking-widest text-muted-foreground">
                                Password
                            </Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={8}
                                autoComplete="current-password"
                                data-testid="login-password-input"
                                className="border-border/70 bg-background"
                            />
                        </div>
                        {error && (
                            <div
                                role="alert"
                                data-testid="login-error"
                                className="rounded-sm border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive"
                            >
                                {error}
                            </div>
                        )}
                        <Button
                            type="submit"
                            disabled={loading}
                            data-testid="login-submit-btn"
                            className="w-full bg-amber text-black hover:bg-amber/90"
                        >
                            {loading ? "Autenticazione…" : "Accedi"}
                        </Button>
                    </form>
                </Card>
                <p className="mt-6 text-center text-xs text-muted-foreground">
                    Non hai ancora un account?{" "}
                    <Link to="/register" className="text-amber hover:underline" data-testid="login-goto-register">
                        Registrati
                    </Link>
                </p>
            </div>
        </div>
    );
}
