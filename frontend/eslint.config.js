// FASE 8G (2026-08-08) — ESLint 9 flat config.
//
// Il progetto era su ESLint 9 ma senza eslint.config.js: `yarn lint`
// falliva all'avvio. Config allineata allo stack reale (CRA+craco,
// React 19 con nuovo JSX runtime, Jest, Tailwind).
//
// Scelte esplicite (non "regole spente all'ingrosso"):
//  * react/recommended + jsx-runtime: niente React import obbligatorio.
//  * react/prop-types off: il progetto non usa PropTypes (mai usati).
//  * react/no-unescaped-entities off: il copy italiano usa apostrofi
//    letterali nel JSX; l'escape forzato peggiorerebbe la leggibilità.
//  * no-unused-vars come ERRORE, con eccezione solo per gli argomenti
//    prefissati "_" (convenzione già usata nel codebase).
const js = require("@eslint/js");
const globals = require("globals");
const react = require("eslint-plugin-react");
const reactHooks = require("eslint-plugin-react-hooks");
const jsxA11y = require("eslint-plugin-jsx-a11y");

module.exports = [
    {
        ignores: ["build/**", "node_modules/**", "coverage/**"],
    },
    js.configs.recommended,
    react.configs.flat.recommended,
    react.configs.flat["jsx-runtime"],
    {
        files: ["src/**/*.{js,jsx}"],
        languageOptions: {
            ecmaVersion: 2023,
            sourceType: "module",
            parserOptions: { ecmaFeatures: { jsx: true } },
            globals: {
                ...globals.browser,
                ...globals.jest,
                process: "readonly",
                module: "readonly",
                require: "readonly",
            },
        },
        plugins: {
            "react-hooks": reactHooks,
            "jsx-a11y": jsxA11y,
        },
        settings: { react: { version: "detect" } },
        rules: {
            ...reactHooks.configs.recommended.rules,
            "react/prop-types": "off",
            "react/no-unescaped-entities": "off",
            "no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
        },
    },
];
