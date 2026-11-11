import { Easing } from "remotion";

export const VIDEO = {
  width: 1080,
  height: 1350,
  fps: 30,
  durationInFrames: 1200,
} as const;

export const COLORS = {
  bg: "#FAFAF9",
  ink: "#111111",
  gray: "#737373",
  line: "#E7E5E4",
  greenBg: "#CDEBD5",
  greenInk: "#1F5133",
  redBg: "#F5D0CE",
  redInk: "#7F1D1D",
  white: "#FFFFFF",
} as const;

// Nomes de família; o carregamento acontece em fonts.ts.
export const FONTS = {
  sans: "Inter, system-ui, sans-serif",
  mono: "'JetBrains Mono', ui-monospace, monospace",
} as const;

export const SAFE = { x: 80, top: 120, bottom: 120 } as const;

export const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);
export const SPRING = { damping: 200, mass: 0.8 } as const;

export const DUR = { enter: 15, exit: 9, stagger: 5, fade: 8 } as const;

// Início (from) e duração de cada cena, em frames — ver ROTEIRO.md.
export const SCENES = {
  S1Hook: { from: 0, duration: 90 },
  S2Pain: { from: 90, duration: 150 },
  S3Question: { from: 240, duration: 90 },
  S4Pipeline: { from: 330, duration: 330 },
  S5Report: { from: 660, duration: 150 },
  S6Metrics: { from: 810, duration: 210 },
  S7Trust: { from: 1020, duration: 90 },
  S8Outro: { from: 1110, duration: 90 },
} as const;
