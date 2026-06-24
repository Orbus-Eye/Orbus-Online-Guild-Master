import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { toast } from "sonner";

export default function PasswordResetConfirm() {
    const [params] = useSearchParams();
    const navigate = useNavigate();
    const [token, setToken] = useState(params.get("token") || "");
    const [pw, setPw] = useState("");
    const [pw2, setPw2] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setErrorMsg("");
        if (pw !== pw2) {
            setErrorMsg("Passwords do not match.");
            return;
        }
        setSubmitting(true);
        try {
            await api.post("/auth/password-reset/confirm", {
                token: token.trim(),
                new_password: pw,
            });
            toast.success("Password reset successful. Please log in.");
            navigate("/login", { replace: true });
        } catch (err) {
            const msg = formatApiError(err);
            setErrorMsg(msg);
            toast.error(msg);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-4 term-grid-bg">
            <div className="w-full max-w-md">
                <Link
                    to="/login"
                    className="text-xs text-muted-foreground hover:text-foreground inline-block mb-6"
                    data-testid="back-login-link"
                >
                    ← back to login
                </Link>

                <div className="border border-border bg-card rounded-sm p-8">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: AUTH / SET NEW PASSWORD
                    </div>
                    <h1 className="text-2xl font-semibold mb-2">Confirm reset</h1>
                    <p className="text-xs text-muted-foreground mb-6">
                        Paste your reset token and choose a new password (min 8 chars,
                        at least one letter and one digit). Check backend logs for your
                        reset token in dev/test mode.
                    </p>

                    <form onSubmit={submit} className="space-y-4" data-testid="pwreset-confirm-form">
                        <div className="space-y-2">
                            <Label htmlFor="token" className="text-xs text-muted-foreground tracking-wider">RESET TOKEN</Label>
                            <textarea
                                id="token"
                                data-testid="pwreset-token-input"
                                required
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                rows={3}
                                className="w-full bg-background border border-border rounded-sm p-3 font-mono text-xs resize-none"
                                placeholder="paste token from email/console"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="pw" className="text-xs text-muted-foreground tracking-wider">NEW PASSWORD</Label>
                            <Input
                                id="pw"
                                data-testid="pwreset-newpw-input"
                                type="password"
                                required
                                autoComplete="new-password"
                                value={pw}
                                onChange={(e) => setPw(e.target.value)}
                                className="bg-background border-border rounded-sm h-11 font-mono"
                                placeholder="••••••••"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="pw2" className="text-xs text-muted-foreground tracking-wider">CONFIRM NEW PASSWORD</Label>
                            <Input
                                id="pw2"
                                data-testid="pwreset-confirmpw-input"
                                type="password"
                                required
                                autoComplete="new-password"
                                value={pw2}
                                onChange={(e) => setPw2(e.target.value)}
                                className="bg-background border-border rounded-sm h-11 font-mono"
                                placeholder="••••••••"
                            />
                        </div>

                        {errorMsg && (
                            <div
                                data-testid="pwreset-error"
                                className="text-xs text-destructive border border-destructive/40 bg-destructive/10 px-3 py-2 rounded-sm"
                            >
                                {errorMsg}
                            </div>
                        )}

                        <Button
                            type="submit"
                            data-testid="pwreset-confirm-submit"
                            disabled={submitting}
                            className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                        >
                            {submitting ? "submitting…" : "Reset password →"}
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
}
