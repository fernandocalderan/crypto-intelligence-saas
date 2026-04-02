import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#07110d",
        ink: "#f2efe5",
        moss: "#b9ff69",
        tide: "#60d8bf",
        slate: "#16211d",
        haze: "#9eb3a8"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(185,255,105,0.12), 0 20px 60px rgba(9,18,14,0.55)"
      },
      borderRadius: {
        "4xl": "2rem"
      }
    }
  },
  plugins: []
};

export default config;

