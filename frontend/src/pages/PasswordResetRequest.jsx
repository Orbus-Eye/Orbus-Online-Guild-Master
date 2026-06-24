import { useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "../lib/api";
import { useT } from "../i18n/I18nContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { toast } from "sonner";

export default function PasswordResetRequest() {
    const { t } = useT();
    const [email, setEmail] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [done, setDone] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await api.post("/auth/password-reset/request", { email: email.trim() });
            setDone(true);
            toast.success(t("password_reset_page.toast_request_sent"));
        } catch (err) {
            toast.error(formatApiError(err));
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
                        :: AUTH / FORGOTTEN PASSWORD
                    </div>
                    <h1 className="text-2xl font-semibold mb-2">{t("password_reset_page.request_title")}</h1>
                    <p className="text-xs text-muted-foreground mb-6">
                        We will not confirm whether the email is registered. If it is,
                        a reset token will be issued.
                    </p>

                    {!done && (
                        <form onSubmit={submit} className="space-y-4" data-testid="pwreset-request-form">
                            <div className="space-y-2">
                                <Label htmlFor="email" className="text-xs text-muted-foreground tracking-wider">EMAIL</Label>
                                <Input
                                    id="email"
                                    data-testid="pwreset-email-input"
                                    type="email"
                                    required
                                    autoComplete="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="bg-background border-border rounded-sm h-11 font-mono"
                                    placeholder="you@orbus.test"
                                />
                            </div>
                            <Button
                                type="submit"
                                data-testid="pwreset-request-submit"
                                disabled={submitting}
                                className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                            >
                                {submitting ? "submitting…" : "Send reset request →"}
                            </Button>
                        </form>
                    )}

                    {done && (
                        <div
                            data-testid="pwreset-request-done"
                            className="space-y-4"
                        >
                            <div className="text-xs text-[#22c55e] border border-[#22c55e]/40 bg-[#22c55e]/10 px-3 py-2 rounded-sm">
                                If that email exists, we&apos;ve sent reset instructions.
                                Check the backend console in dev/test mode for the token.
                            </div>
                            <Link to="/password-reset/confirm">
                                <Button
                                    data-testid="pwreset-goto-confirm"
                                    className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                                >
                                    I have a token →
                                </Button>
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
