import { useEffect, useRef, useState } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Team, fetchMyTeam } from "../api/client";
import { STADIUM_LEVELS } from "../gameData";
import AmbientGlow from "../components/AmbientGlow";
import AnimatedNumber from "../components/AnimatedNumber";
import GameClock from "../components/GameClock";
import PageTransition from "../components/PageTransition";
import PlayerAvatar from "../components/PlayerAvatar";
import { SkeletonDashboard } from "../components/Skeleton";
import Sidebar, { TabKey } from "../components/Sidebar";
import { Card } from "../components/ui";
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
      <AmbientGlow />
      <div
        className="relative z-10 flex min-h-screen"
        style={teamThemeStyle(team.primary_color, team.secondary_color)}
      >
        <Sidebar team={team} activeTab={tab} onTabChange={setTab} />

        <div className="min-w-0 flex-1">
          <PageTransition>
            <div className="mx-auto max-w-5xl px-4 py-8 lg:px-8">
              <div className="mb-6 pl-12 lg:pl-0">
                <Card className="flex flex-wrap items-center gap-4">
                  <PlayerAvatar firstName={team.name} lastName="" photoUrl={team.logo_url} size={60} />
                  <div className="min-w-0 flex-1">
                    <h1 className="truncate text-2xl font-bold text-slate-100 sm:text-3xl">{team.name}</h1>
                    <p className="mt-1 flex flex-wrap items-center gap-1.5 text-slate-400">
                      <span className="font-stat text-lg font-semibold text-slate-100">
                        <AnimatedNumber value={team.franchise_capital} suffix=" FT" />
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
                      <span className="text-sm">
                        · Stadion szint <span className="font-stat">{team.stadium_level}</span> (
                        <span className="font-stat">
                          {STADIUM_LEVELS[team.stadium_level].capacity.toLocaleString("hu-HU")}
                        </span>{" "}
                        néző) ·{" "}
                        <span className="font-stat">
                          {team.wins}Gy {team.losses}V {team.ties}D
                        </span>
                      </span>
                    </p>
                    <p className="text-xs text-slate-500">
                      Napi fenntartás (fizetések): -{team.daily_salary_cost.toLocaleString("hu-HU")} FT
                    </p>
                  </div>
                  <p className="whitespace-nowrap text-xs text-slate-500">
                    Játékidő: <GameClock />
                  </p>
                </Card>
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
