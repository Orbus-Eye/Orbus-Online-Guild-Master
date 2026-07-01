// Round 11.4a — Preventive XSS sanitizer helper.
//
// Currently the codebase does NOT use dangerouslySetInnerHTML anywhere
// (verified Round 11.4a). React's default text-escaping is the active
// defense. This helper exists so that if a future component absolutely
// needs HTML rendering (rich-text editor, server-rendered markdown, etc.)
// it has a single audited entry point.
//
// Usage:
//   import { sanitize } from "../utils/safeHtml";
//   <div dangerouslySetInnerHTML={{ __html: sanitize(html) }} />
//
// Allowed tags / attrs are intentionally minimal. Add new ones only after
// security review.

import DOMPurify from "dompurify";

const ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "br", "p", "span"];
const ALLOWED_ATTR = ["href", "target", "rel", "class"];

export function sanitize(html) {
    if (typeof html !== "string") return "";
    return DOMPurify.sanitize(html, {
        ALLOWED_TAGS,
        ALLOWED_ATTR,
        ALLOW_DATA_ATTR: false,
    });
}
