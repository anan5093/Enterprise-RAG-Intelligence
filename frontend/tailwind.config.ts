import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101318",
        panel: "#171b22",
        line: "#303743",
        paper: "#f7f3eb",
        mint: "#7bdcb5",
        amber: "#f4b860",
        coral: "#ef6f6c"
      }
    },
  },
  plugins: [],
};

export default config;

