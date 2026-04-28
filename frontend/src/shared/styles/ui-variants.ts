/**
 * Semantic visual contracts for the shared product design system.
 */

export const PREMIUM_UI = {
  pageWrapper:
    "relative min-h-screen overflow-hidden bg-[color:var(--color-background)] text-[color:var(--color-on-background)] font-sans selection:bg-primary/20",
  page: "mx-auto w-full max-w-[var(--container-max)] px-4 md:px-6 xl:px-[var(--space-gutter)]",
  section: "space-y-6",

  card: {
    base: "relative overflow-hidden rounded-[var(--radius-lg)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] text-[color:var(--color-on-surface)]",
    hover: "transition-colors duration-200 hover:bg-[color:var(--color-surface-container-high)]",
    padding: "p-6 md:p-8",
  },

  button: {
    premium:
      "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] border border-transparent bg-[color:var(--color-primary)] px-6 py-2 text-sm font-semibold text-[color:var(--color-on-primary)] transition-[background-color,border-color,color,transform] duration-200 outline-none hover:bg-[color:var(--color-primary-container)] active:translate-y-px disabled:pointer-events-none disabled:opacity-50",
    glass:
      "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-high)] px-6 py-2 text-sm font-semibold text-[color:var(--color-on-surface)] transition-[background-color,border-color,color,transform] duration-200 outline-none hover:bg-[color:var(--color-surface-container-highest)] active:translate-y-px disabled:pointer-events-none disabled:opacity-50",
    ghost:
      "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] border border-transparent bg-transparent px-4 py-2 text-sm font-medium text-[color:var(--color-on-surface-variant)] transition-[background-color,color,transform] duration-200 outline-none hover:bg-[color:var(--color-surface-container)] hover:text-[color:var(--color-on-surface)] active:translate-y-px active:bg-[color:var(--color-surface-container-high)] disabled:pointer-events-none disabled:opacity-50",
  },

  grid: {
    bento: "grid grid-cols-2 md:grid-cols-4 gap-4 auto-rows-[minmax(120px,auto)]",
    stack: "flex flex-col gap-4",
  },

  text: {
    label: "text-[13px] font-medium uppercase tracking-[0.05em] text-[color:var(--color-on-surface-variant)]",
    heading: "text-[32px] font-semibold tracking-[-0.01em] text-[color:var(--color-on-surface)]",
    title: "text-[18px] font-semibold text-[color:var(--color-on-surface)]",
    body: "text-[16px] leading-[1.6] text-[color:var(--color-on-surface-variant)]",
    value: "text-[40px] md:text-[56px] font-semibold tracking-[-0.03em] leading-none text-[color:var(--color-on-surface)]",
    subvalue: "text-[13px] font-medium uppercase tracking-[0.05em] text-[color:var(--color-outline)]",
  },

  badge: {
    base: "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.05em] leading-none",
    glass: "border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-high)] text-[color:var(--color-on-surface-variant)]",
    success: "border-[color:var(--color-secondary)]/30 bg-[color:var(--color-secondary)]/12 text-[color:var(--color-secondary)]",
    warning: "border-[color:var(--color-tertiary)]/30 bg-[color:var(--color-tertiary)]/12 text-[color:var(--color-tertiary)]",
  },

  animation: {
    fadeIn: "animate-in fade-in duration-500",
    slideUp: "animate-in slide-in-from-bottom-4 duration-500",
  },
};
