/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'fungal-dark': '#0b0f0c',
        'glow-mint': '#8cffda',
        'neural-violet': '#7a5cff',
        'muted-white': '#e0e0e0',
      },
      fontFamily: {
        heading: ['Poppins', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.05)', opacity: '.9' },
        },
        'spore-float': {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)', opacity: '0.6' },
          '50%': { transform: 'translateY(-10px) rotate(180deg)', opacity: '1' },
        },
        'mycelial-grow': {
          '0%': { transform: 'scale(0.8)', opacity: '0.3' },
          '50%': { transform: 'scale(1.1)', opacity: '0.8' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'organic-breathe': {
          '0%, 100%': { transform: 'scale(1) rotate(0deg)' },
          '33%': { transform: 'scale(1.02) rotate(1deg)' },
          '66%': { transform: 'scale(0.98) rotate(-1deg)' },
        },
        'button-glow': {
          '0%': { boxShadow: '0 0 10px rgba(140, 255, 218, 0.2)' },
          '50%': {
            boxShadow: '0 0 35px rgba(140, 255, 218, 0.7)',
            transform: 'translateY(-2px)'
          },
          '100%': { boxShadow: '0 0 20px 5px rgba(140, 255, 218, 0.4)' },
        },
        'text-shimmer': {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center',
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center',
          },
        },
        'shimmer': {
          '0%': { 'background-position': '200% 0' },
          '100%': { 'background-position': '-200% 0' },
        },
        'ambient-glow': {
          '0%, 100%': {
            'box-shadow': '0 0 20px rgba(140, 255, 218, 0.15), 0 0 5px rgba(122, 92, 255, 0.1)',
          },
          '50%': {
            'box-shadow': '0 0 35px rgba(140, 255, 218, 0.25), 0 0 10px rgba(122, 92, 255, 0.2)',
          },
        },
      },
      animation: {
        'pulse-slow': 'pulse-slow 3s infinite',
        'button-glow': 'button-glow 4s ease-in-out infinite',
        'text-shimmer': 'shimmer 3s ease-out infinite alternate',
        'diagram-glow': 'ambient-glow 6s infinite alternate',
        'spore-float': 'spore-float 4s ease-in-out infinite',
        'mycelial-grow': 'mycelial-grow 2s ease-out',
        'organic-breathe': 'organic-breathe 6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}