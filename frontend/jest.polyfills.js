// Polyfill per l'ambiente jsdom di Jest 27 (react-scripts 5):
// react-router v7 richiede TextEncoder/TextDecoder, assenti in jsdom.
// Caricato via `setupFiles` (vedi craco.config.js) PRIMA dei moduli di test.
const { TextEncoder, TextDecoder } = require("util");

if (typeof global.TextEncoder === "undefined") {
    global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === "undefined") {
    global.TextDecoder = TextDecoder;
}
