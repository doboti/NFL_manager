/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        gridiron: {
          field: "#0f2e1e",
          accent: "#34d399",
          cyan: "#22d3ee",
        },
      },
      keyframes: {
        shimmer: {
          "0%": { transform: "translateX(-150%) skewX(-20deg)" },
          "100%": { transform: "translateX(250%) skewX(-20deg)" },
        },
      },
      animation: {
        shimmer: "shimmer 2.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
