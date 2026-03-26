import globals from "globals";

export default [
  {
    files: ["static/js/**/*.js"],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: "module",
      globals: {
        ...globals.browser,
        console: "readonly",
        setTimeout: "readonly",
        setInterval: "readonly",
        localStorage: "readonly",
        fetch: "readonly",
        URLSearchParams: "readonly",
        Blob: "readonly",
        FormData: "readonly",
        FileReader: "readonly",
        Image: "readonly",
        matchMedia: "readonly",
        CustomEvent: "readonly",
        dispatchEvent: "readonly",
        document: "readonly",
        window: "readonly",
        location: "readonly",
        history: "readonly",
        navigator: "readonly",
        showToast: "readonly",
        toggleLoading: "readonly",
        showSection: "readonly",
        escapeHtml: "readonly",
        loadCookies: "readonly",
        getCached: "readonly",
        setCache: "readonly",
        getDefaultRepliesAPI: "readonly"
      }
    },
    rules: {
      "no-unused-vars": ["warn", { "argsIgnorePattern": "^_", "caughtErrorsIgnorePattern": "^_" }],
      "no-undef": "warn"
    }
  }
];
