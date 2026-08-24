import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Team, fetchMyTeam } from "../api/client";
import { STADIUM_LEVELS } from "../gameData";
import { useAuth } from "../context/AuthContext";
import AnimatedNumber from "../components/AnimatedNumber";
import GameClock from "../components/GameClock";
import PageTransition from "../components/PageTransition";
import { SkeletonDashboard } from "../components/Skeleton";
import OverviewTab from "./dashboard/OverviewTab";
import RosterTab from "./dashboard/RosterTab";
import MarketTab from "./dashboard/MarketTab";
import TradesTab from "./dashboard/TradesTab";
import MatchesTab from "./dashboard/MatchesTab";
import LeagueTab from "./dashboard/LeagueTab";

type TabKey = "overview" | "roster" | "market" | "trades" | "matches" | "league";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Áttekintés" },
  { key: "league", label: "Liga" },
  { key: "roster", label: "Keret" },
  { key: "market", label: "Piac" },
  { key: "trades", label: "Tárgyalások" },
  { key: "matches", label: "Meccsek" },
];

export default function Dashboard() {
  const [team, setTeam] = useState<Team | null>(null);
  const [tab, setTab] = useState<TabKey>("overview");
  const [error, setError] = useState<string | null>(null);
  const { logout } = useAuth();

  useEffect(() => {
    fetchMyTeam()
      .then(setTeam)
      .catch(() => setError("Nem sikerült betölteni a franchise adatait."));
  }, []);

  if (error && !team) return <p className="p-8 text-red-400">{error}</p>;
  if (!team) return <SkeletonDashboard />;

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gridiron-accent">{team.name}</h1>
            <p className="text-slate-400">
              Franchise Tőke: <AnimatedNumber value={team.franchise_capital} suffix=" FT" /> · Stadion szint{" "}
              {team.stadium_level} ({STADIUM_LEVELS[team.stadium_level].capacity.toLocaleString("hu-HU")} néző) ·{" "}
              {team.wins}Gy {team.losses}V {team.ties}D
            </p>
            <p className="text-xs text-slate-500">
              Napi fenntartás (fizetések): -{team.daily_salary_cost.toLocaleString("hu-HU")} FT
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <p className="text-xs text-slate-500">
              Játékidő: <GameClock />
            </p>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              onClick={logout}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-red-400 hover:text-red-400"
            >
              Kijelentkezés
            </motion.button>
          </div>
        </div>

        <div className="mb-8 flex flex-wrap gap-2 border-b border-slate-800 pb-3">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition ${
                tab === t.key
                  ? "bg-gridiron-accent text-slate-950"
                  : "text-slate-400 hover:text-gridiron-accent"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "overview" && <OverviewTab team={team} onTeamUpdate={setTeam} />}
        {tab === "league" && <LeagueTab team={team} />}
        {tab === "roster" && <RosterTab team={team} onTeamUpdate={setTeam} />}
        {tab === "market" && <MarketTab team={team} onTeamUpdate={setTeam} />}
        {tab === "trades" && <TradesTab team={team} onTeamUpdate={setTeam} />}
        {tab === "matches" && <MatchesTab team={team} />}
      </div>
    </PageTransition>
  );
}
