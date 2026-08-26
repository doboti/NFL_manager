export type PlayerTier = "elite" | "gold" | "silver" | "bronze" | "common";

export function getPlayerTier(overall: number): PlayerTier {
  if (overall >= 95) return "elite";
  if (overall >= 90) return "gold";
  if (overall >= 80) return "silver";
  if (overall >= 70) return "bronze";
  return "common";
}

interface TierStyle {
  card: string;
  ovr: string;
  meta: string;
  glow: string;
  shimmer: boolean;
}

export const TIER_STYLES: Record<PlayerTier, TierStyle> = {
  elite: {
    card: "bg-gradient-to-br from-fuchsia-400 via-purple-500 to-violet-800 border-fuchsia-300 text-white shadow-[0_0_20px_rgba(217,70,239,0.35)]",
    ovr: "text-white drop-shadow-[0_0_6px_rgba(255,255,255,0.6)]",
    meta: "text-purple-100/80",
    glow: "rgba(217,70,239,0.55)",
    shimmer: true,
  },
  gold: {
    card: "bg-gradient-to-br from-yellow-200 via-amber-400 to-yellow-600 border-yellow-200 text-slate-900",
    ovr: "text-yellow-950",
    meta: "text-slate-800/80",
    glow: "rgba(250,204,21,0.5)",
    shimmer: true,
  },
  silver: {
    card: "bg-gradient-to-br from-slate-100 via-slate-300 to-slate-400 border-slate-100 text-slate-900",
    ovr: "text-slate-800",
    meta: "text-slate-700/80",
    glow: "rgba(203,213,225,0.4)",
    shimmer: false,
  },
  bronze: {
    card: "bg-gradient-to-br from-orange-200 via-orange-400 to-orange-600 border-orange-200 text-slate-900",
    ovr: "text-orange-950",
    meta: "text-slate-800/80",
    glow: "rgba(251,146,60,0.4)",
    shimmer: false,
  },
  common: {
    card: "bg-slate-900 border-slate-800 text-slate-100",
    ovr: "text-gridiron-accent",
    meta: "text-slate-400",
    glow: "rgba(52,211,153,0.25)",
    shimmer: false,
  },
};
