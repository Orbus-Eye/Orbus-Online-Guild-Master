import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";

export default function Landing() {
    const { user } = useAuth();

    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <header className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="text-amber">◆</span>
                    <span data-testid="brand-tag">ORBUS // GUILDMASTER</span>
                </div>
                <div className="text-xs text-muted-foreground hidden sm:block">
                    v0.1 · phase-1
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
                    A text-based guild management MMO. Recruit adventurers, send them on
                    dungeon runs, hoard gold, and grow your reputation across the realms.
                    No graphics. Just numbers, logs, and decisions.
                </p>

                <div className="mt-10 flex flex-col sm:flex-row gap-3">
                    {user ? (
                        <Link to="/dashboard">
                            <Button
                                data-testid="landing-dashboard-btn"
                                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm px-6 h-11"
                            >
                                Enter Dashboard →
                            </Button>
                        </Link>
                    ) : (
                        <>
                            <Link to="/register">
                                <Button
                                    data-testid="landing-register-btn"
                                    className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm px-6 h-11"
                                >
                                    Register
                                </Button>
                            </Link>
                            <Link to="/login">
                                <Button
                                    data-testid="landing-login-btn"
                                    variant="outline"
                                    className="rounded-sm px-6 h-11 border-border bg-transparent hover:bg-secondary"
                                >
                                    Login
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
                        ▸ View public leaderboard →
                    </Link>
                </div>

                <section className="mt-20 grid sm:grid-cols-3 gap-4 text-sm">
                    {[
                        { k: "01", title: "Recruit", desc: "Hire adventurers with unique stats and quirks." },
                        { k: "02", title: "Dispatch", desc: "Send parties into dungeons. Read the after-action report." },
                        { k: "03", title: "Grow", desc: "Upgrade your hall, earn reputation, beat rivals." },
                    ].map((b) => (
                        <div
                            key={b.k}
                            className="border border-border bg-card p-5 rounded-sm"
                        >
                            <div className="text-amber text-xs mb-2 tracking-widest">
                                ::{b.k}
                            </div>
                            <div className="text-foreground font-medium mb-1">
                                {b.title}
                            </div>
                            <div className="text-muted-foreground text-xs leading-relaxed">
                                {b.desc}
                            </div>
                        </div>
                    ))}
                </section>
            </main>

            <footer className="max-w-5xl mx-auto px-6 py-6 text-xs text-muted-foreground border-t border-border">
                <span className="text-amber">$</span> orbus --phase 1 --status ready
            </footer>
        </div>
    );
}
