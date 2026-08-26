import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  DivisionStandings,
  PlayoffMatch,
  ScheduledMatch,
  SeasonHistoryEntry,
  SeasonStatus,
  Team,
  TeamRoster,
  fetchTeamRoster,
  getLeagueSchedule,
  getPlayoffBracket,
  getSeasonHistory,
  getSeasonStatus,
  getStandings,
} from "../../api/client";
import { CalendarClock, History, Trophy } from "lucide-react";
import { Card, SectionHeading } from "../../components/ui";
import { SkeletonBlock } from "../../components/Skeleton";
import { useVirtualTime } from "../../context/TimeContext";

interface Props {
  team: Team;
}

const PLAYOFF_ROUND_LABELS: Record<string, string> = {
  conference_semifinal: "Konferencia elődöntő",
  conference_final: "Konferencia döntő",
  super_bowl: "Super Bowl",
};

const PLAYOFF_RESULT_LABELS: Record<string, string> = {
  missed_playoffs: "Nem jutott rájátszásba",
  conference_semifinal: "Konferencia elődöntő",
  conference_final: "Konferencia döntő",
  runner_up: "Super Bowl vesztes",
  champion: "Bajnok",
};

const PHASE_LABELS: Record<string, string> = {
  REGULAR: "Alapszakasz",
  PLAYOFFS: "Rájátszás",
};

const PLAYOFF_ROUND_ORDER = ["conference_semifinal", "conference_final", "super_bowl"];

function winPct(t: { wins: number; losses: number; ties: number }): number {
  const games = t.wins + t.losses + t.ties;
  if (games === 0) return 0;
  return (t.wins + t.ties * 0.5) / games;
}

export default function LeagueTab({ team }: Props) {
  const [season, setSeason] = useState<SeasonStatus | null>(null);
  const [standings, setStandings] = useState<DivisionStandings[] | null>(null);
  const [schedule, setSchedule] = useState<ScheduledMatch[] | null>(null);
  const [history, setHistory] = useState<SeasonHistoryEntry[] | null>(null);
  const [playoffs, setPlayoffs] = useState<PlayoffMatch[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rosterModalOpen, setRosterModalOpen] = useState(false);
  const [rosterView, setRosterView] = useState<TeamRoster | null>(null);
  const [rosterError, setRosterError] = useState<string | null>(null);
  const { virtualNow } = useVirtualTime();

  useEffect(() => {
    Promise.all([getSeasonStatus(), getStandings(), getLeagueSchedule(), getSeasonHistory(), getPlayoffBracket()])
      .then(([seasonData, standingsData, scheduleData, historyData, playoffData]) => {
        setSeason(seasonData);
        setStandings(standingsData);
        setSchedule(scheduleData);
        setHistory(historyData);
        setPlayoffs(playoffData);
      })
      .catch(() => setError("Nem sikerült betölteni a liga adatait."));
  }, []);

  async function openRoster(teamId: number) {
    setRosterModalOpen(true);
    setRosterView(null);
    setRosterError(null);
    try {
      setRosterView(await fetchTeamRoster(teamId));
    } catch {
      setRosterError("Nem sikerült betölteni a csapat rosterét.");
    }
  }

  function closeRoster() {
    setRosterModalOpen(false);
    setRosterView(null);
    setRosterError(null);
  }

  const conferences = standings ? Array.from(new Set(standings.map((d) => d.conference))) : [];

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      {season && (
        <Card className="mb-6">
          <h2 className="mb-1 font-semibold">
            {season.season}. szezon · {PHASE_LABELS[season.phase]}
          </h2>
          <p className="text-sm text-slate-400">
            {season.phase === "REGULAR"
              ? `${season.season_day}. / ${season.regular_season_days}. nap`
              : season.current_playoff_round
              ? PLAYOFF_ROUND_LABELS[season.current_playoff_round] ?? season.current_playoff_round
              : ""}
          </p>
        </Card>
      )}

      {playoffs !== null && playoffs.length > 0 && (
        <>
          <SectionHeading icon={Trophy}>Rájátszás</SectionHeading>
          <div className="mb-8 grid gap-4 md:grid-cols-3">
            {PLAYOFF_ROUND_ORDER.filter((round) => playoffs.some((m) => m.playoff_round === round)).map((round) => (
              <div key={round}>
                <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-400">
                  {PLAYOFF_ROUND_LABELS[round] ?? round}
                </h3>
                <div className="space-y-2">
                  {playoffs
                    .filter((m) => m.playoff_round === round)
                    .map((m) => {
                      const mine = m.home_team_id === team.id || m.away_team_id === team.id;
                      const homeWon = m.played && (m.home_score ?? 0) > (m.away_score ?? 0);
                      const awayWon = m.played && (m.away_score ?? 0) > (m.home_score ?? 0);
                      return (
                        <Card key={m.id} highlight={mine} className="text-sm">
                          <div className={`flex items-center justify-between ${homeWon ? "font-bold text-team-text" : "text-slate-300"}`}>
                            <button onClick={() => openRoster(m.home_team_id)} className="truncate text-left hover:underline">
                              {m.home_team_name}
                            </button>
                            {m.played && <span>{m.home_score}</span>}
                          </div>
                          <div className={`mt-1 flex items-center justify-between ${awayWon ? "font-bold text-team-text" : "text-slate-300"}`}>
                            <button onClick={() => openRoster(m.away_team_id)} className="truncate text-left hover:underline">
                              {m.away_team_name}
                            </button>
                            {m.played && <span>{m.away_score}</span>}
                          </div>
                          {!m.played && (
                            <div className="mt-1 text-right text-[10px] text-slate-500">
                              {new Date(m.scheduled_at).toLocaleString("hu-HU")}
                            </div>
                          )}
                        </Card>
                      );
                    })}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <SectionHeading>Állás</SectionHeading>
      {standings === null ? (
        <div className="mb-8 space-y-2">
          <SkeletonBlock className="h-40 w-full" />
        </div>
      ) : (
        <div className="mb-8 grid gap-6 lg:grid-cols-2">
          {conferences.map((conference) => (
            <div key={conference}>
              <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-400">{conference}</h3>
              <div className="space-y-4">
                {standings
                  .filter((d) => d.conference === conference)
                  .map((division) => (
                    <Card key={division.division} className="p-3">
                      <div className="mb-2 text-xs font-semibold text-slate-500">{division.division}</div>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-[10px] uppercase text-slate-600">
                            <th className="pb-1 font-medium">Csapat</th>
                            <th className="pb-1 text-right font-medium">Gy</th>
                            <th className="pb-1 text-right font-medium">V</th>
                            <th className="pb-1 text-right font-medium">D</th>
                            <th className="pb-1 text-right font-medium">Ø OVR</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[...division.teams]
                            .sort((a, b) => winPct(b) - winPct(a))
                            .map((t) => (
                              <tr
                                key={t.id}
                                className={
                                  t.id === team.id
                                    ? "border-l-2 border-team-primary bg-team-primary/10 font-bold text-team-text"
                                    : "text-slate-300"
                                }
                              >
                                <td className="py-0.5 truncate">
                                  <button
                                    onClick={() => openRoster(t.id)}
                                    className="truncate text-left hover:underline"
                                  >
                                    {t.name}
                                  </button>
                                  {t.is_bot && <span className="ml-1 text-[10px] text-gridiron-cyan">AI</span>}
                                </td>
                                <td className="py-0.5 text-right">{t.wins}</td>
                                <td className="py-0.5 text-right">{t.losses}</td>
                                <td className="py-0.5 text-right">{t.ties}</td>
                                <td className="py-0.5 text-right text-slate-500">{t.avg_overall ?? "–"}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </Card>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <SectionHeading icon={CalendarClock}>Sorsolás</SectionHeading>
      {schedule === null ? (
        <div className="space-y-2">
          <SkeletonBlock className="h-10 w-full" />
          <SkeletonBlock className="h-10 w-full" />
        </div>
      ) : schedule.length === 0 ? (
        <p className="text-sm text-slate-500">Nincs még kiírt meccs.</p>
      ) : (
        <div className="space-y-2">
          {schedule.map((m, i) => {
            const mine = m.home_team_id === team.id || m.away_team_id === team.id;
            return (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: Math.min(i, 15) * 0.03 }}
                className={`flex items-center justify-between rounded-lg border p-3 text-sm ${
                  mine ? "border-team-primary bg-team-primary/10 text-team-text" : "border-slate-800 bg-slate-900 text-slate-300"
                }`}
              >
                <span>
                  {m.is_playoff && (
                    <span className="mr-2 rounded bg-gridiron-cyan/20 px-1.5 py-0.5 text-[10px] font-bold uppercase text-gridiron-cyan">
                      {m.playoff_round ? PLAYOFF_ROUND_LABELS[m.playoff_round] ?? m.playoff_round : "Rájátszás"}
                    </span>
                  )}
                  {m.home_team_name} — {m.away_team_name}
                </span>
                <span className="text-xs opacity-70">{new Date(m.scheduled_at).toLocaleString("hu-HU")}</span>
              </motion.div>
            );
          })}
        </div>
      )}

      {history !== null && history.length > 0 && (
        <>
          <SectionHeading icon={History} className="mt-8">Korábbi szezonok</SectionHeading>
          <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-900/70">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase text-slate-600">
                  <th className="p-3 font-medium">Szezon</th>
                  <th className="p-3 font-medium">Mérleg</th>
                  <th className="p-3 font-medium">Eredmény</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.season} className="border-t border-slate-800 text-slate-300">
                    <td className="p-3">{h.season}.</td>
                    <td className="p-3">
                      {h.wins}Gy {h.losses}V {h.ties}D
                    </td>
                    <td className={h.playoff_result === "champion" ? "p-3 font-bold text-team-text" : "p-3"}>
                      {PLAYOFF_RESULT_LABELS[h.playoff_result] ?? h.playoff_result}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <AnimatePresence>
        {rosterModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
            onClick={closeRoster}
          >
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              onClick={(e) => e.stopPropagation()}
              className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-xl border border-slate-800 bg-slate-900 p-4"
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{rosterView?.name ?? "Roster"}</h3>
                <button onClick={closeRoster} className="text-slate-400 hover:text-slate-200">
                  Bezárás
                </button>
              </div>

              {rosterError && <p className="text-sm text-red-400">{rosterError}</p>}

              {!rosterView && !rosterError && (
                <div className="space-y-2">
                  <SkeletonBlock className="h-8 w-full" />
                  <SkeletonBlock className="h-8 w-full" />
                  <SkeletonBlock className="h-8 w-full" />
                </div>
              )}

              {rosterView && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[10px] uppercase text-slate-600">
                      <th className="pb-1 font-medium">Név</th>
                      <th className="pb-1 font-medium">Poszt</th>
                      <th className="pb-1 text-right font-medium">Kor</th>
                      <th className="pb-1 text-right font-medium">OVR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...rosterView.players]
                      .sort((a, b) => b.overall - a.overall)
                      .map((p) => (
                        <tr key={p.id} className="border-t border-slate-800 text-slate-300">
                          <td className="py-1">
                            {p.first_name} {p.last_name}
                            {p.is_starter && (
                              <span className="ml-1 text-[10px] text-gridiron-accent">kezdő</span>
                            )}
                            {p.injured_until && new Date(p.injured_until).getTime() > virtualNow() && (
                              <span className="ml-1 text-[10px] text-red-400">sérült</span>
                            )}
                          </td>
                          <td className="py-1 text-slate-500">{p.position}</td>
                          <td className="py-1 text-right">{p.age}</td>
                          <td className="py-1 text-right font-semibold text-gridiron-accent">{p.overall}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
