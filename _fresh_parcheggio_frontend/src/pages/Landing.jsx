import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function Landing() {
    return (
        <div className="min-h-screen bg-background text-foreground term-grid-bg term-scanline">
            <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-between px-6 py-10">
                <header className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                        <span className="text-amber">orbus</span>::terminal
                    </span>
                    <span className="hidden text-[10px] text-muted-foreground sm:inline">
                        v0.1 · fase 1
                    </span>
                </header>

                <section className="flex flex-1 flex-col justify-center py-16">
                    <p className="mb-4 text-xs uppercase tracking-widest text-muted-foreground">
                        &gt; boot sequence
                    </p>
                    <h1
                        data-testid="landing-title"
                        className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl"
                    >
                        Orbus Online<span className="text-amber">.</span>
                        <br />
                        <span className="text-muted-foreground">Guild Master</span>
                        <span className="caret-blink" />
                    </h1>
                    <p
                        data-testid="landing-tagline"
                        className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg"
                    >
                        Un MMO gestionale testuale. Fonda una gilda, recluta avventurieri,
                        rispedisci ogni notte le tue squadre nei dungeon più oscuri.
                        Nessuna grafica: solo scelte, numeri e rapporti dopo lo scontro.
                    </p>

                    <div className="mt-10 flex flex-col gap-3 sm:flex-row">
                        <Link to="/register">
                            <Button
                                size="lg"
                                data-testid="landing-register-btn"
                                className="min-w-[180px] bg-amber text-black hover:bg-amber/90"
                            >
                                Fonda la tua gilda
                            </Button>
                        </Link>
                        <Link to="/login">
                            <Button
                                size="lg"
                                variant="outline"
                                data-testid="landing-login-btn"
                                className="min-w-[180px] border-border text-foreground hover:bg-secondary"
                            >
                                Accedi
                            </Button>
                        </Link>
                    </div>
                </section>

                <footer className="border-t border-border/60 pt-6 text-[11px] uppercase tracking-widest text-muted-foreground">
                    &gt; sistema pronto · in ascolto su porta 8001
                </footer>
            </div>
        </div>
    );
}
