import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        critical: "#dc2626",
        alert: "#f59e0b",
        info: "#3b82f6",
        healthy: "#10b981",
      },
    },
  },
  plugins: [],
};

export default config;
