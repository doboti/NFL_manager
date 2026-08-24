export type PlayerTier = "gold" | "silver" | "bronze" | "common";

export function getPlayerTier(overall: number): PlayerTier {
  if (overall >= 90) return "gold";
  if (overall >= 80) return "silver";
  if (overall >= 70) return "bronze";
  return "common";
}

interface TierStyle {
  card: string;
  ovr: string;
  meta: string;
  shimmer: boolean;
}

export const TIER_STYLES: Record<PlayerTier, TierStyle> = {
  gold: {
    card: "bg-gradient-to-br from-yellow-200 via-amber-400 to-yellow-600 border-yellow-200 text-slate-900",
    ovr: "text-yellow-950",
    meta: "text-slate-800/80",
    shimmer: true,
  },
  silver: {
    card: "bg-gradient-to-br from-slate-100 via-slate-300 to-slate-400 border-slate-100 text-slate-900",
    ovr: "text-slate-800",
    meta: "text-slate-700/80",
    shimmer: false,
  },
  bronze: {
    card: "bg-gradient-to-br from-orange-200 via-orange-400 to-orange-600 border-orange-200 text-slate-900",
    ovr: "text-orange-950",
    meta: "text-slate-800/80",
    shimmer: false,
  },
  common: {
    card: "bg-slate-900 border-slate-800 text-slate-100",
    ovr: "text-gridiron-accent",
    meta: "text-slate-400",
    shimmer: false,
  },
};
