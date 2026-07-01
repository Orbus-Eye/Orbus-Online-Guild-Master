/* ROUND 11.2 TASK 8 — SEO meta-tag manager (zero-dep).
 *
 * Imperatively sets <title>, <meta name="description">, Open Graph,
 * Twitter Card and <link rel="canonical"> on mount, and restores the
 * previous values on unmount. Mirrors the `react-helmet-async` API for
 * the small subset we actually need (title + description + og + twitter
 * + canonical) without pulling in the dependency.
 *
 * Why imperative: Googlebot (and Bing) execute JavaScript during render
 * before snapshotting the DOM, so tags injected here ARE indexed. For
 * crawlers that don't execute JS (rare in 2026), the `index.html`
 * default tags act as a safe fallback.
 */
import { useEffect } from "react";


function _upsertMeta({ name, property, content }) {
    if (content == null) return null;
    const selector = name
        ? `meta[name="${name}"]`
        : `meta[property="${property}"]`;
    let el = document.head.querySelector(selector);
    const created = !el;
    if (!el) {
        el = document.createElement("meta");
        if (name) el.setAttribute("name", name);
        if (property) el.setAttribute("property", property);
        document.head.appendChild(el);
    }
    const prev = el.getAttribute("content");
    el.setAttribute("content", content);
    return { el, prev, created };
}


function _upsertCanonical(href) {
    if (!href) return null;
    let el = document.head.querySelector('link[rel="canonical"]');
    const created = !el;
    if (!el) {
        el = document.createElement("link");
        el.setAttribute("rel", "canonical");
        document.head.appendChild(el);
    }
    const prev = el.getAttribute("href");
    el.setAttribute("href", href);
    return { el, prev, created };
}


export default function SeoHead({
    title,
    description,
    canonical,
    ogTitle,
    ogDescription,
    ogUrl,
    ogType = "article",
    ogSiteName = "Orbus Online: Guild Master",
    twitterCard = "summary",
}) {
    useEffect(() => {
        // Snapshot for restore on unmount.
        const prevTitle = document.title;
        if (title) document.title = title;
        const records = [];
        if (description) records.push(_upsertMeta({ name: "description", content: description }));
        if (ogTitle || title) records.push(_upsertMeta({ property: "og:title", content: ogTitle || title }));
        if (ogDescription || description) records.push(_upsertMeta({ property: "og:description", content: ogDescription || description }));
        if (ogUrl || canonical) records.push(_upsertMeta({ property: "og:url", content: ogUrl || canonical }));
        if (ogType) records.push(_upsertMeta({ property: "og:type", content: ogType }));
        if (ogSiteName) records.push(_upsertMeta({ property: "og:site_name", content: ogSiteName }));
        if (twitterCard) records.push(_upsertMeta({ name: "twitter:card", content: twitterCard }));
        if (twitterCard && (ogTitle || title)) records.push(_upsertMeta({ name: "twitter:title", content: ogTitle || title }));
        if (twitterCard && (ogDescription || description)) records.push(_upsertMeta({ name: "twitter:description", content: ogDescription || description }));
        const canonRec = _upsertCanonical(canonical);
        return () => {
            document.title = prevTitle;
            for (const r of records) {
                if (!r) continue;
                if (r.created) r.el.remove();
                else if (r.prev != null) r.el.setAttribute("content", r.prev);
            }
            if (canonRec) {
                if (canonRec.created) canonRec.el.remove();
                else if (canonRec.prev != null) canonRec.el.setAttribute("href", canonRec.prev);
            }
        };
    }, [title, description, canonical, ogTitle, ogDescription, ogUrl, ogType, ogSiteName, twitterCard]);

    return null;
}
