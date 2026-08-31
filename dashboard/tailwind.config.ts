import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        paper: "var(--paper)",
        panel: "var(--panel)",
        ink: "var(--ink)",
        muted: "var(--ink-muted)",
        rule: "var(--rule)",
        focus: "var(--focus)",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "sans-serif"],
        serif: ["IBM Plex Serif", "serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      maxWidth: { content: "1200px" },
    },
  },
  plugins: [],
};

export default config;
