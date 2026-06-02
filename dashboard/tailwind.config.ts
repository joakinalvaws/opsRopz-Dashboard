import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        critical: "#dc2626",
        alert: "#f59e0b",
        info: "#3b82f6",
      },
    },
  },
  plugins: [],
};

export default config;
