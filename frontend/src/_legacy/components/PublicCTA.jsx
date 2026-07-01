/* ROUND 11.2 TASK 8 — Reusable conversion CTA block.
 *
 * Two side-by-side buttons (stacked on mobile). Used on the public
 * `/traits` and `/stats` pages, both in the hero and in the footer
 * to capture conversion at multiple scroll points.
 */
import { Link } from "react-router-dom";


export default function PublicCTA({ headline, subline, location = "hero" }) {
    return (
        <div
            data-testid={`public-cta-${location}`}
            className="border border-border rounded-sm bg-card/60 p-5 sm:p-7"
        >
            <p
                data-testid={`public-cta-${location}-headline`}
                className="text-lg sm:text-xl font-semibold tracking-tight text-amber"
            >
                {headline}
            </p>
            {subline && (
                <p className="text-sm text-muted-foreground mt-2">{subline}</p>
            )}
            <div className="mt-4 flex flex-col sm:flex-row gap-2 sm:gap-3">
                <Link
                    to="/register"
                    data-testid={`public-cta-${location}-register`}
                    className="bg-amber/90 hover:bg-amber text-background px-5 py-2.5 rounded-sm text-sm font-semibold text-center"
                >
                    🛡 Crea account
                </Link>
                <Link
                    to="/login"
                    data-testid={`public-cta-${location}-login`}
                    className="border border-border hover:border-amber/60 hover:text-amber px-5 py-2.5 rounded-sm text-sm text-center"
                >
                    Accedi
                </Link>
            </div>
        </div>
    );
}
