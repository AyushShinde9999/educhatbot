/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          700: '#0369a1',
          800: '#0d3b66',
          900: '#092c4e',
        }
      }
    },
  },
  plugins: [],
}
