import { useEffect, useRef, useState } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Team, fetchMyTeam } from "../api/client";
import { STADIUM_LEVELS } from "../gameData";
import AnimatedNumber from "../components/AnimatedNumber";
import GameClock from "../components/GameClock";
import PageTransition from "../components/PageTransition";
import { SkeletonDashboard } from "../components/Skeleton";
import Sidebar, { TabKey } from "../components/Sidebar";
import { TeamThemeProvider } from "../context/TeamThemeContext";
import { teamThemeStyle } from "../teamTheme";
import OverviewTab from "./dashboard/OverviewTab";
import RosterTab from "./dashboard/RosterTab";
import MarketTab from "./dashboard/MarketTab";
import TradesTab from "./dashboard/TradesTab";
import MatchesTab from "./dashboard/MatchesTab";
import LeagueTab from "./dashboard/LeagueTab";

export default function Dashboard() {
  const [team, setTeam] = useState<Team | null>(null);
  const [tab, setTab] = useState<TabKey>("overview");
  const [error, setError] = useState<string | null>(null);
  const [capitalTrend, setCapitalTrend] = useState<{ direction: "up" | "down"; delta: number } | null>(null);
  const prevCapitalRef = useRef<number | null>(null);

  useEffect(() => {
    fetchMyTeam()
      .then(setTeam)
      .catch(() => setError("Nem sikerült betölteni a franchise adatait."));
  }, []);

  useEffect(() => {
    if (!team) return;
    if (prevCapitalRef.current !== null && team.franchise_capital !== prevCapitalRef.current) {
      const delta = team.franchise_capital - prevCapitalRef.current;
      setCapitalTrend({ direction: delta > 0 ? "up" : "down", delta: Math.abs(delta) });
      const timeout = setTimeout(() => setCapitalTrend(null), 5000);
      prevCapitalRef.current = team.franchise_capital;
      return () => clearTimeout(timeout);
    }
    prevCapitalRef.current = team.franchise_capital;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team?.franchise_capital]);

  if (error && !team) return <p className="p-8 text-red-400">{error}</p>;
  if (!team) return <SkeletonDashboard />;

  return (
    <TeamThemeProvider primary={team.primary_color} secondary={team.secondary_color}>
      <div
        className="flex min-h-screen bg-slate-950"
        style={teamThemeStyle(team.primary_color, team.secondary_color)}
      >
        <Sidebar team={team} activeTab={tab} onTabChange={setTab} />

        <div className="min-w-0 flex-1">
          <PageTransition>
            <div className="mx-auto max-w-5xl px-4 py-8 lg:px-8">
              <div className="mb-6 flex flex-wrap items-center justify-between gap-4 pl-12 lg:pl-0">
                <div>
                  <h1 className="text-2xl font-bold text-slate-100">{team.name}</h1>
                  <p className="flex flex-wrap items-center gap-1 text-slate-400">
                    <span>
                      Franchise Tőke: <AnimatedNumber value={team.franchise_capital} suffix=" FT" />
                    </span>
                    {capitalTrend && (
                      <span
                        className={`flex items-center gap-0.5 text-xs font-semibold ${
                          capitalTrend.direction === "up" ? "text-emerald-400" : "text-red-400"
                        }`}
                      >
                        {capitalTrend.direction === "up" ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                        {capitalTrend.delta.toLocaleString("hu-HU")}
                      </span>
                    )}
                    <span>
                      · Stadion szint {team.stadium_level} (
                      {STADIUM_LEVELS[team.stadium_level].capacity.toLocaleString("hu-HU")} néző) · {team.wins}Gy{" "}
                      {team.losses}V {team.ties}D
                    </span>
                  </p>
                  <p className="text-xs text-slate-500">
                    Napi fenntartás (fizetések): -{team.daily_salary_cost.toLocaleString("hu-HU")} FT
                  </p>
                </div>
                <p className="whitespace-nowrap text-xs text-slate-500">
                  Játékidő: <GameClock />
                </p>
              </div>

              {tab === "overview" && <OverviewTab team={team} onTeamUpdate={setTeam} />}
              {tab === "league" && <LeagueTab team={team} />}
              {tab === "roster" && <RosterTab team={team} onTeamUpdate={setTeam} />}
              {tab === "market" && <MarketTab team={team} onTeamUpdate={setTeam} />}
              {tab === "trades" && <TradesTab team={team} onTeamUpdate={setTeam} />}
              {tab === "matches" && <MatchesTab team={team} />}
            </div>
          </PageTransition>
        </div>
      </div>
    </TeamThemeProvider>
  );
}
