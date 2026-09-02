/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ── Enterprise Cybersecurity Design System ──────────────────────
        // Centralized palette — change once, update everywhere.
        cv: {
          // Backgrounds
          bg:         '#F6F8FA', // Main page background (light gray)
          card:       '#FFFFFF', // Card/panel surface
          sidebar:    '#17212B', // Sidebar / nav background

          // Text
          text:       '#17212B', // Primary text
          muted:      '#667085', // Secondary / muted text

          // Borders
          border:     '#E4E7EC', // Default border

          // Brand / Action
          blue:       '#2563EB', // Primary action / links / active nav
          blueLight:  '#DBEAFE', // Soft blue tint for badges/hover

          // Semantic
          success:    '#16A34A', // Healthy / compliant
          successBg:  '#DCFCE7', // Light green background
          warning:    '#D97706', // Warning states
          warningBg:  '#FEF3C7', // Light amber background
          danger:     '#DC2626', // Critical / error
          dangerBg:   '#FEE2E2', // Light red background
          info:       '#0891B2', // Informational / cyan
          infoBg:     '#CFFAFE', // Light cyan background

          // Sidebar-specific text colors (dark background)
          sideText:   '#94A3B8', // Muted text on dark sidebar
          sideActive: '#FFFFFF', // Active/selected text on sidebar
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', 'Consolas', 'monospace'],
        sans: ['Inter', '"IBM Plex Sans"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'card':    '0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px -1px rgba(0,0,0,0.06)',
        'card-md': '0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)',
        'card-lg': '0 10px 15px -3px rgba(0,0,0,0.07), 0 4px 6px -4px rgba(0,0,0,0.05)',
      },
      borderRadius: {
        'card': '8px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
