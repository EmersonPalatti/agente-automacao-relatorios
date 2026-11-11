import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";

const inter = loadInter("normal", {
  subsets: ["latin"],
  weights: ["400", "600", "800"],
});

const jetBrainsMono = loadJetBrainsMono("normal", {
  subsets: ["latin"],
  weights: ["500", "700"],
});

/** Famílias resolvidas pelo loader. Os componentes usam os nomes de `theme.ts`. */
export const loadedFonts = {
  sans: inter.fontFamily,
  mono: jetBrainsMono.fontFamily,
};
