/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#10151c",
        panel: "#161c25",
        line: "#26303d",
        accent: "#ff7a45",
        ok: "#3ddc97",
        warn: "#ffc24b",
        danger: "#ff5d5d",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
}
