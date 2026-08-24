import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  DivisionStandings,
  ScheduledMatch,
  SeasonHistoryEntry,
  SeasonStatus,
  Team,
  getLeagueSchedule,
  getSeasonHistory,
  getSeasonStatus,
  getStandings,
} from "../../api/client";
import { SkeletonBlock } from "../../components/Skeleton";

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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getSeasonStatus(), getStandings(), getLeagueSchedule(), getSeasonHistory()])
      .then(([seasonData, standingsData, scheduleData, historyData]) => {
        setSeason(seasonData);
        setStandings(standingsData);
        setSchedule(scheduleData);
        setHistory(historyData);
      })
      .catch(() => setError("Nem sikerült betölteni a liga adatait."));
  }, []);

  const conferences = standings ? Array.from(new Set(standings.map((d) => d.conference))) : [];

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      {season && (
        <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900 p-4">
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
        </div>
      )}

      <h2 className="mb-3 text-xl font-semibold">Állás</h2>
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
                    <div key={division.division} className="rounded-lg border border-slate-800 bg-slate-900 p-3">
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
                                className={t.id === team.id ? "font-bold text-gridiron-accent" : "text-slate-300"}
                              >
                                <td className="py-0.5 truncate">
                                  {t.name}
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
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <h2 className="mb-3 text-xl font-semibold">Sorsolás</h2>
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
                  mine ? "border-gridiron-accent bg-gridiron-accent/10 text-gridiron-accent" : "border-slate-800 bg-slate-900 text-slate-300"
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
          <h2 className="mb-3 mt-8 text-xl font-semibold">Korábbi szezonok</h2>
          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900">
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
                    <td className={h.playoff_result === "champion" ? "p-3 font-bold text-gridiron-accent" : "p-3"}>
                      {PLAYOFF_RESULT_LABELS[h.playoff_result] ?? h.playoff_result}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
