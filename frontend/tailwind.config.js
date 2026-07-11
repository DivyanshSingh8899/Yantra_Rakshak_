/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: { light: "#fcfcfb", dark: "#1a1a19" },
        status: {
          good: "#0ca30c",
          warning: "#fab219",
          critical: "#d03b3b",
        },
      },
    },
  },
  plugins: [],
};
