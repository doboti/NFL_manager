export const STADIUM_LEVELS: Record<
  number,
  { capacity: number; baseRevenue: number; upgradeCost: number; upgradeHours: number }
> = {
  1: { capacity: 10_000, baseRevenue: 50_000, upgradeCost: 0, upgradeHours: 0 },
  2: { capacity: 25_000, baseRevenue: 125_000, upgradeCost: 500_000, upgradeHours: 12 },
  3: { capacity: 50_000, baseRevenue: 250_000, upgradeCost: 2_000_000, upgradeHours: 24 },
  4: { capacity: 80_000, baseRevenue: 400_000, upgradeCost: 5_000_000, upgradeHours: 48 },
};
export const MAX_STADIUM_LEVEL = 4;

// Mirrors backend/app/core/progression.py: SLOT_LEVEL_REQUIREMENTS.
export const SLOT_LEVEL_REQUIREMENTS: Record<number, number> = { 1: 1, 2: 5, 3: 15 };

export const TACTIC_LABELS: Record<string, string> = {
  BALANCED: "Kiegyensúlyozott",
  PASS_HEAVY: "Passz-orientált",
  RUN_HEAVY: "Futás-orientált",
  BLITZ: "Blitz védekezés",
  PREVENT: "Prevent védekezés",
};
