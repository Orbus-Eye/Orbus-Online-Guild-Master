// ROUND 6A.2c — Pre-deploy lint gate. Flat config (ESLint 9.x).
// Catches the bug classes that bit us this sprint:
//   - react/jsx-no-undef       → Admin.jsx `t()` no-scope
//   - react-hooks/rules-of-hooks → hooks inside conditionals
//   - no-undef                 → silent reference errors
//   - react/jsx-uses-vars      → imported component flagged unused
import js from "@eslint/js";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import globals from "globals";

export default [
    {
        ignores: [
            "build/**",
            "dist/**",
            "node_modules/**",
            "coverage/**",
            "public/**",
        ],
    },
    js.configs.recommended,
    {
        files: ["src/**/*.{js,jsx}"],
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "module",
            globals: {
                ...globals.browser,
                ...globals.node,
                ...globals.jest,
                process: "readonly",
            },
            parserOptions: {
                ecmaFeatures: { jsx: true },
            },
        },
        plugins: {
            react: reactPlugin,
            "react-hooks": reactHooksPlugin,
        },
        settings: { react: { version: "detect" } },
        rules: {
            ...reactPlugin.configs.recommended.rules,
            ...reactHooksPlugin.configs.recommended.rules,
            "react/jsx-uses-vars": "error",
            "react/jsx-no-undef": "error",
            "react/jsx-closing-tag-location": "warn",
            "react/react-in-jsx-scope": "off", // React 17+ auto JSX runtime
            "react/prop-types": "off",          // codebase doesn't use PropTypes
            "react/no-unknown-property": ["error", { ignore: ["jsx", "global"] }],
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
            "no-undef": "error",
            "no-unused-vars": ["warn", {
                argsIgnorePattern: "^_",
                varsIgnorePattern: "^_",
                caughtErrorsIgnorePattern: "^_?[a-z]?$",
                destructuredArrayIgnorePattern: "^_",
            }],
            "no-empty": ["warn", { allowEmptyCatch: true }],
        },
    },
];
