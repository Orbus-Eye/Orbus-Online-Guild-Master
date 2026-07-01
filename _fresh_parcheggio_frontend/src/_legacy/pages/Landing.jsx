import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Landing() {
    const { user } = useAuth();
    const { t } = useT();

    const features = [
        { k: "01", titleKey: "landing.feature_recruit_title", descKey: "landing.feature_recruit_desc" },
        { k: "02", titleKey: "landing.feature_dispatch_title", descKey: "landing.feature_dispatch_desc" },
        { k: "03", titleKey: "landing.feature_grow_title", descKey: "landing.feature_grow_desc" },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <header className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="text-amber">◆</span>
                    <span data-testid="brand-tag">ORBUS // GUILDMASTER</span>
                </div>
                <div className="flex items-center gap-3">
                    <LanguageSwitcher />
                    <div className="text-xs text-muted-foreground hidden sm:block">
                        v0.12 · i18n
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 pt-16 pb-24">
                <div className="text-xs text-muted-foreground tracking-widest mb-4">
                    [ TEXT-BASED MMO · GUILD MANAGEMENT ]
                </div>

                <h1
                    data-testid="landing-title"
                    className="text-4xl sm:text-5xl lg:text-6xl font-semibold leading-tight tracking-tight"
                >
                    Orbus Online:
                    <br />
                    <span className="text-amber">Guild Master</span>
                    <span className="caret-blink align-baseline" />
                </h1>

                <p className="mt-6 max-w-2xl text-base text-muted-foreground leading-relaxed">
                    {t("landing.description_1")} {t("landing.description_2")}
                </p>

                <div className="mt-10 flex flex-col sm:flex-row gap-3">
                    {user ? (
                        <Link to="/dashboard">
                            <Button
                                data-testid="landing-dashboard-btn"
                                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm px-6 h-11"
                            >
                                {t("landing.cta_dashboard")} →
                            </Button>
                        </Link>
                    ) : (
                        <>
                            <Link to="/register">
                                <Button
                                    data-testid="landing-register-btn"
                                    className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm px-6 h-11"
                                >
                                    {t("landing.cta_register")}
                                </Button>
                            </Link>
                            <Link to="/login">
                                <Button
                                    data-testid="landing-login-btn"
                                    variant="outline"
                                    className="rounded-sm px-6 h-11 border-border bg-transparent hover:bg-secondary"
                                >
                                    {t("landing.cta_login")}
                                </Button>
                            </Link>
                        </>
                    )}
                </div>

                <div className="mt-4">
                    <Link
                        to="/leaderboard"
                        data-testid="landing-leaderboard-link"
                        className="text-xs text-muted-foreground hover:text-amber tracking-widest underline-offset-4 hover:underline"
                    >
                        ▸ {t("landing.cta_leaderboard")} →
                    </Link>
                </div>

                <section className="mt-20 grid sm:grid-cols-3 gap-4 text-sm">
                    {features.map((b) => (
                        <div
                            key={b.k}
                            className="border border-border bg-card p-5 rounded-sm"
                        >
                            <div className="text-amber text-xs mb-2 tracking-widest">
                                ::{b.k}
                            </div>
                            <div className="text-foreground font-medium mb-1">
                                {t(b.titleKey)}
                            </div>
                            <div className="text-muted-foreground text-xs leading-relaxed">
                                {t(b.descKey)}
                            </div>
                        </div>
                    ))}
                </section>
            </main>

            <footer className="max-w-5xl mx-auto px-6 py-6 text-xs text-muted-foreground border-t border-border">
                <span className="text-amber">$</span> orbus --phase 12 --status ready
            </footer>
        </div>
    );
}
