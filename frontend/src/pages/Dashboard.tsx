import { useEffect, useState } from "react";
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

  useEffect(() => {
    fetchMyTeam()
      .then(setTeam)
      .catch(() => setError("Nem sikerült betölteni a franchise adatait."));
  }, []);

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
                  <p className="text-slate-400">
                    Franchise Tőke: <AnimatedNumber value={team.franchise_capital} suffix=" FT" /> · Stadion szint{" "}
                    {team.stadium_level} ({STADIUM_LEVELS[team.stadium_level].capacity.toLocaleString("hu-HU")}{" "}
                    néző) · {team.wins}Gy {team.losses}V {team.ties}D
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
