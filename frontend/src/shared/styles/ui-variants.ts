/**
 * UI Variants and Constants for the Premium Design System.
 * Bridging CSS Utilities with TypeScript for semantic styling.
 */

export const PREMIUM_UI = {
  // Base background with ambient light effects
  pageWrapper: "min-h-screen bg-[#09090b] text-zinc-50 font-sans selection:bg-white/20 relative overflow-hidden",
  
  // Card styles (Glassmorphism)
  card: {
    base: "glass-card",
    hover: "glass-card-hover",
    padding: "p-6 md:p-8",
  },

  // Button styles
  button: {
    premium: "btn-premium",
    glass: "btn-glass",
    ghost: "btn-ghost",
  },

  // Layout structures
  grid: {
    bento: "grid grid-cols-2 md:grid-cols-4 gap-4 auto-rows-[minmax(120px,auto)]",
    stack: "flex flex-col gap-4",
  },

  // Typography
  text: {
    label: "text-premium-label",
    heading: "text-premium-heading",
    value: "text-premium-value",
    subvalue: "text-zinc-500 font-bold text-lg uppercase tracking-widest",
  },

  // Icons and Badges
  badge: {
    base: "px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider border leading-none shadow-sm",
    glass: "bg-white/10 border-white/10 text-white",
    success: "bg-emerald-400/10 border-emerald-400/20 text-emerald-400",
    warning: "bg-orange-400/10 border-orange-400/20 text-orange-400",
  },

  // Animations
  animation: {
    fadeIn: "animate-in fade-in duration-500",
    slideUp: "animate-in slide-in-from-bottom-4 duration-500",
  }
};
