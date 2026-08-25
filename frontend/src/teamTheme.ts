import { CSSProperties } from "react";

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  return [r, g, b];
}

export function hexToRgbTriplet(hex: string): string {
  const [r, g, b] = hexToRgb(hex);
  return `${r} ${g} ${b}`;
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// WCAG relative luminance -- picks black or white text so it stays legible
// against a team's primary color regardless of how light or dark it is.
export function contrastText(hex: string): "#000000" | "#ffffff" {
  return relativeLuminance(hex) > 0.4 ? "#000000" : "#ffffff";
}

function mixWithWhite(hex: string, amount: number): string {
  const [r, g, b] = hexToRgb(hex);
  const mix = (c: number) => Math.round(c + (255 - c) * amount);
  return `#${[mix(r), mix(g), mix(b)]
    .map((c) => c.toString(16).padStart(2, "0"))
    .join("")}`;
}

// A lot of real team colors (navy, black) are too dark to read as TEXT on
// this app's already-dark background -- pick whichever of primary/secondary
// is lighter, then brighten it further if it's still too dark, so the
// "your team" accent color always stays legible regardless of which team.
export function readableAccentHex(primaryHex: string, secondaryHex: string): string {
  let candidate = relativeLuminance(primaryHex) >= relativeLuminance(secondaryHex) ? primaryHex : secondaryHex;
  let guard = 0;
  while (relativeLuminance(candidate) < 0.4 && guard < 8) {
    candidate = mixWithWhite(candidate, 0.25);
    guard += 1;
  }
  return candidate;
}

export function teamThemeStyle(primaryHex: string, secondaryHex: string): CSSProperties {
  return {
    "--team-primary-rgb": hexToRgbTriplet(primaryHex),
    "--team-secondary-rgb": hexToRgbTriplet(secondaryHex),
    "--team-text-rgb": hexToRgbTriplet(readableAccentHex(primaryHex, secondaryHex)),
  } as CSSProperties;
}
