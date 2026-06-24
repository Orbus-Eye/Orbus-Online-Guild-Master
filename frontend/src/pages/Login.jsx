import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Login() {
    const { login, formatApiError } = useAuth();
    const { t } = useT();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setErrorMsg("");
        setSubmitting(true);
        try {
            await login(email.trim(), password);
            toast.success(t("auth.toast_login_success"));
            navigate("/dashboard", { replace: true });
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
                <div className="flex items-center justify-between mb-6">
                    <Link
                        to="/"
                        className="text-xs text-muted-foreground hover:text-foreground"
                        data-testid="back-home-link"
                    >
                        ← {t("common.back")}
                    </Link>
                    <LanguageSwitcher />
                </div>

                <div className="border border-border bg-card rounded-sm p-8">
                    <div className="text-xs text-amber tracking-widest mb-2">
                        :: AUTH / SIGN-IN
                    </div>
                    <h1 className="text-2xl font-semibold mb-6">{t("auth.login_title")}</h1>

                    <form onSubmit={submit} className="space-y-4" data-testid="login-form">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-xs text-muted-foreground tracking-wider">
                                {t("auth.email").toUpperCase()}
                            </Label>
                            <Input
                                id="email"
                                data-testid="login-email-input"
                                type="email"
                                required
                                autoComplete="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="bg-background border-border rounded-sm h-11 font-mono"
                                placeholder="you@orbus.test"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-xs text-muted-foreground tracking-wider">
                                {t("auth.password").toUpperCase()}
                            </Label>
                            <Input
                                id="password"
                                data-testid="login-password-input"
                                type="password"
                                required
                                autoComplete="current-password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="bg-background border-border rounded-sm h-11 font-mono"
                                placeholder="••••••••"
                            />
                        </div>

                        {errorMsg && (
                            <div
                                data-testid="login-error"
                                className="text-xs text-destructive border border-destructive/40 bg-destructive/10 px-3 py-2 rounded-sm"
                            >
                                {errorMsg}
                            </div>
                        )}

                        <Button
                            type="submit"
                            data-testid="login-submit-btn"
                            disabled={submitting}
                            className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                        >
                            {submitting ? t("common.loading") : `${t("auth.submit_login")} →`}
                        </Button>
                    </form>

                    <div className="mt-6 text-xs text-muted-foreground flex items-center justify-between gap-3 flex-wrap">
                        <div>
                            {t("auth.no_account")}{" "}
                            <Link
                                to="/register"
                                className="text-amber hover:underline"
                                data-testid="goto-register-link"
                            >
                                {t("auth.go_register")}
                            </Link>
                        </div>
                        <Link
                            to="/password-reset/request"
                            className="text-muted-foreground hover:text-amber hover:underline"
                            data-testid="forgot-password-link"
                        >
                            {t("auth.forgot_password")}
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
