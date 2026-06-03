export const colors = {
  // light defaults — dark vem via CSS vars no globals.css
  bg: "#FAFAF7",
  surface: "#FFFFFF",
  surfaceInverted: "#0A0E1A",
  border: "#E5E7EB",
  borderStrong: "#CBD5E1",
  text: "#0A0E1A",
  textMuted: "#4B5563",
  accent: "#FF6B35",
  accentHover: "#E55A2A",
  info: "#1E40AF",
  success: "#10B981",
  danger: "#DC2626",
} as const;

export const fontSizes = {
  xs: "0.75rem",
  sm: "0.875rem",
  base: "1rem",
  lg: "clamp(1.0625rem, 0.95rem + 0.5vw, 1.125rem)",
  xl: "clamp(1.25rem, 1.15rem + 0.45vw, 1.375rem)",
  "2xl": "clamp(1.5rem, 1.35rem + 0.75vw, 1.75rem)",
  "3xl": "clamp(1.875rem, 1.5rem + 1.875vw, 2.5rem)",
  "4xl": "clamp(2.375rem, 1.75rem + 3.125vw, 3.5rem)",
  display: "clamp(3rem, 2.25rem + 3.75vw, 4.5rem)",
  hero: "clamp(3.5rem, 2.5rem + 5vw, 6rem)",
} as const;

export const space = [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128] as const;

export const radii = {
  sm: "0.375rem",
  md: "0.625rem",
  lg: "1rem",
  pill: "9999px",
} as const;

export const motionDurations = {
  fast: "150ms",
  base: "250ms",
  slow: "400ms",
} as const;

export const easings = {
  outExpo: "cubic-bezier(0.16, 1, 0.3, 1)",
} as const;

export const breakpoints = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
} as const;
