// ROUND 6B.3 Wave 3 (post-deploy hotfix) — Standalone Chronicle page.
//
// Why a dedicated page? `ChronicleCard` was previously only accessible as
// a fold-in widget on the Dashboard. Production smoke flagged P1: direct
// navigation to `/chronicle` redirected to landing (no route registered,
// catch-all `*` → "/"). This page reuses the existing card with a larger
// limit and a proper page chrome so the chronicle is bookmarkable and
// reachable from the global nav.
import AppHeader from "@/components/AppHeader";
import ChronicleCard from "@/components/ChronicleCard";
import { useT } from "@/i18n/I18nContext";

export default function Chronicle() {
    const { t } = useT();
    return (
        <div className="min-h-screen bg-background text-foreground">
            <AppHeader subtitleKey="nav.brand_subtitle_dashboard" />
            <main
                className="max-w-5xl mx-auto px-4 sm:px-6 py-6 font-mono"
                data-testid="chronicle-page"
            >
                <header className="mb-6">
                    <div className="text-[10px] text-amber tracking-widest mb-2">
                        :: {t("chronicle.title")}
                    </div>
                    <h1 className="text-3xl font-semibold tracking-tight">
                        {t("chronicle.page_title", "Cronaca del Server")}
                    </h1>
                    <p className="text-[12px] text-muted-foreground mt-2 max-w-2xl">
                        {t(
                            "chronicle.page_intro",
                            "Feed pubblico in sola lettura degli eventi recenti del server: spedizioni completate, raid vinti, achievement sbloccati, milestone delle altre gilde.",
                        )}
                    </p>
                </header>
                <ChronicleCard limit={50} />
            </main>
        </div>
    );
}
