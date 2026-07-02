import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import PasswordInput from "../components/PasswordInput";
import PasswordChecklist from "../components/PasswordChecklist";
import { checkPasswordPolicy, PASSWORD_POLICY_MESSAGE } from "../lib/passwordPolicy";
import { toast } from "sonner";

export default function PasswordResetConfirm() {
    const { t } = useT();
    const [params] = useSearchParams();
    const navigate = useNavigate();
    const [token, setToken] = useState(params.get("token") || "");
    const [pw, setPw] = useState("");
    const [pw2, setPw2] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const pwPolicy = checkPasswordPolicy(pw);
    const canSubmit = pwPolicy.allValid && pw === pw2 && token.trim().length > 0 && !submitting;

    const submit = async (e) => {
        e.preventDefault();
        setErrorMsg("");
        // ROUND 16.5.4a — validazione client mirror del backend
        if (!pwPolicy.allValid) {
            setErrorMsg(`Password non valida: ${PASSWORD_POLICY_MESSAGE}`);
            return;
        }
        if (pw !== pw2) {
            setErrorMsg("Le password non coincidono.");
            return;
        }
        setSubmitting(true);
        try {
            await api.post("/auth/password-reset/confirm", {
                token: token.trim(),
                new_password: pw,
            });
            toast.success(t("password_reset_page.toast_reset_success"));
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
                    <h1 className="text-2xl font-semibold mb-2">{t("password_reset_page.confirm_title")}</h1>
                    <p className="text-xs text-muted-foreground mb-6">
                        Incolla il token del reset e scegli una nuova password.
                        In modalità dev/test il token viene stampato nei log del backend.
                    </p>

                    <form onSubmit={submit} className="space-y-4" data-testid="pwreset-confirm-form">
                        <div className="space-y-2">
                            <Label htmlFor="token" className="text-xs text-muted-foreground tracking-wider">{t("password_reset_page.token_label")}</Label>
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
                            <Label htmlFor="pw" className="text-xs text-muted-foreground tracking-wider">{t("password_reset_page.new_password_label")}</Label>
                            <PasswordInput
                                id="pw"
                                testid="pwreset-newpw-input"
                                required
                                autoComplete="new-password"
                                value={pw}
                                onChange={(e) => setPw(e.target.value)}
                            />
                            <div className="text-[10px] text-muted-foreground tracking-wider mt-2">
                                REQUISITI PASSWORD
                            </div>
                            <PasswordChecklist
                                password={pw}
                                testid="pwreset-password-checklist"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="pw2" className="text-xs text-muted-foreground tracking-wider">{t("password_reset_page.confirm_password_label")}</Label>
                            <PasswordInput
                                id="pw2"
                                testid="pwreset-confirmpw-input"
                                required
                                autoComplete="new-password"
                                value={pw2}
                                onChange={(e) => setPw2(e.target.value)}
                            />
                            {pw2 && pw2 !== pw && (
                                <div
                                    data-testid="pwreset-mismatch-hint"
                                    className="text-[11px] text-destructive"
                                >
                                    Le password non coincidono.
                                </div>
                            )}
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
                            disabled={!canSubmit}
                            className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? "invio…" : "Reimposta password →"}
                        </Button>
                    </form>
                </div>
            </div>
        </div>
    );
}
