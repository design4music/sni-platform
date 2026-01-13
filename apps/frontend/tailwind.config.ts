import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        dashboard: {
          bg: '#0a0e1a',
          surface: '#111827',
          border: '#1f2937',
          text: '#f9fafb',
          'text-muted': '#9ca3af',
        },
        reading: {
          bg: '#ffffff',
          surface: '#f9fafb',
          border: '#e5e7eb',
          text: '#111827',
          'text-muted': '#6b7280',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};

export default config;
