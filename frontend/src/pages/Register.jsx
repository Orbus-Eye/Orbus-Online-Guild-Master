import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import PasswordInput from "../components/PasswordInput";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Register() {
    const { register, formatApiError } = useAuth();
    const { t } = useT();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setErrorMsg("");
        if (password.length < 8) {
            setErrorMsg(t("auth.errors.weak_password"));
            return;
        }
        if (password !== confirmPassword) {
            setErrorMsg(t("auth.errors.password_mismatch"));
            return;
        }
        setSubmitting(true);
        try {
            await register(email.trim(), username.trim(), password);
            toast.success(t("auth.toast_register_success"));
            navigate("/create-guild", { replace: true });
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
                        :: AUTH / NEW-MASTER
                    </div>
                    <h1 className="text-2xl font-semibold mb-6">{t("auth.register_title")}</h1>

                    <form onSubmit={submit} className="space-y-4" data-testid="register-form">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-xs text-muted-foreground tracking-wider">
                                {t("auth.email").toUpperCase()}
                            </Label>
                            <Input
                                id="email"
                                data-testid="register-email-input"
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
                            <Label htmlFor="username" className="text-xs text-muted-foreground tracking-wider">
                                {t("auth.username").toUpperCase()}
                            </Label>
                            <Input
                                id="username"
                                data-testid="register-username-input"
                                type="text"
                                required
                                minLength={2}
                                maxLength={32}
                                autoComplete="username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="bg-background border-border rounded-sm h-11 font-mono"
                                placeholder="guildmaster_01"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-xs text-muted-foreground tracking-wider">
                                {t("auth.password").toUpperCase()}{" "}
                                <span className="text-muted-foreground">({t("auth.password_min")})</span>
                            </Label>
                            <PasswordInput
                                id="password"
                                testid="register-password-input"
                                required
                                minLength={8}
                                autoComplete="new-password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="confirm_password" className="text-xs text-muted-foreground tracking-wider">
                                {t("auth.confirm_password").toUpperCase()}
                            </Label>
                            <PasswordInput
                                id="confirm_password"
                                name="confirm_password"
                                testid="register-confirm-password-input"
                                required
                                minLength={8}
                                autoComplete="new-password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </div>

                        {errorMsg && (
                            <div
                                data-testid="register-error"
                                className="text-xs text-destructive border border-destructive/40 bg-destructive/10 px-3 py-2 rounded-sm"
                            >
                                {errorMsg}
                            </div>
                        )}

                        <Button
                            type="submit"
                            data-testid="register-submit-btn"
                            disabled={submitting}
                            className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                        >
                            {submitting ? t("common.loading") : `${t("auth.submit_register")} →`}
                        </Button>
                    </form>

                    <div className="mt-6 text-xs text-muted-foreground">
                        {t("auth.have_account")}{" "}
                        <Link
                            to="/login"
                            className="text-amber hover:underline"
                            data-testid="goto-login-link"
                        >
                            {t("auth.go_login")}
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
