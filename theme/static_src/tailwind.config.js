/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html',
    '../**/templates/**/*.html',
    '../**/forms.py',
  ],
  theme: {
    extend: {
      colors: {
        laspad: {
          green: '#1a6b3a',
          gold:  '#c9a227',
          dark:  '#0f1f15',
        },
      },
      fontFamily: {
        sora: ['Sora', 'sans-serif'],
        dm:   ['DM Sans', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
