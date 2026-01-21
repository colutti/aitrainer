/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)', // Using CSS variables if defined in index.css, or verify usage
        secondary: 'var(--color-secondary)',
        'dark-bg': '#121212', // Fallback or as defined
        'light-bg': '#1E1E1E',
        'text-primary': '#FFFFFF',
        'text-secondary': '#A0A0A0',
        // Add other custom colors used in the app if they were relying on CDN defaults or custom config
      },
      // Mimic any custom config the CDN might have had or defaults
    },
  },
  plugins: [],
}
