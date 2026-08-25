import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CalendarDays, Swords } from "lucide-react";
import { Match, PracticeMatchResult, Team, listMatches, playPracticeMatch } from "../../api/client";
import MatchViewer from "../../components/MatchViewer";
import { SkeletonBlock } from "../../components/Skeleton";
import { Card, PrimaryButton, SectionHeading } from "../../components/ui";

interface Props {
  team: Team;
}

const PLAYOFF_ROUND_LABELS: Record<string, string> = {
  conference_semifinal: "Konferencia elődöntő",
  conference_final: "Konferencia döntő",
  super_bowl: "Super Bowl",
};

export default function MatchesTab({ team }: Props) {
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [practiceResult, setPracticeResult] = useState<PracticeMatchResult | null>(null);
  const [expandedMatchId, setExpandedMatchId] = useState<number | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMatches()
      .then(setMatches)
      .catch(() => setError("Nem sikerült betölteni a meccs történetet."));
  }, []);

  async function withBusy(key: string, action: () => Promise<void>) {
    setBusy(key);
    setError(null);
    try {
      await action();
    } catch {
      setError("A művelet nem sikerült.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <SectionHeading icon={Swords}>Gyakorló meccs</SectionHeading>
      <Card className="mb-8">
        <PrimaryButton
          disabled={busy === "practice"}
          onClick={() => withBusy("practice", async () => setPracticeResult(await playPracticeMatch()))}
        >
          {busy === "practice" ? "Szimuláció..." : "Gyakorló meccs indítása"}
        </PrimaryButton>

        <AnimatePresence>
          {practiceResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-4 overflow-hidden"
            >
              <MatchViewer
                homeTeamName={team.name}
                awayTeamName={practiceResult.opponent_name}
                homeScore={practiceResult.home_score}
                awayScore={practiceResult.away_score}
                playLog={practiceResult.play_log}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      <SectionHeading icon={CalendarDays}>Meccs történet</SectionHeading>
      {matches === null ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <SkeletonBlock key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : matches.length === 0 ? (
        <p className="text-sm text-slate-500">Még nem volt liga-meccs.</p>
      ) : (
        <div className="space-y-2">
          {matches.map((m) => {
            const expanded = expandedMatchId === m.id;
            return (
              <Card key={m.id} className="p-3 text-sm text-slate-300">
                <button
                  className="flex w-full items-center justify-between text-left"
                  onClick={() => setExpandedMatchId(expanded ? null : m.id)}
                >
                  <span>
                    {m.is_playoff && (
                      <span className="mr-2 rounded bg-gridiron-cyan/20 px-1.5 py-0.5 text-[10px] font-bold uppercase text-gridiron-cyan">
                        {m.playoff_round ? PLAYOFF_ROUND_LABELS[m.playoff_round] ?? m.playoff_round : "Rájátszás"}
                      </span>
                    )}
                    {m.home_team_name} {m.home_score} - {m.away_score} {m.away_team_name}
                  </span>
                  <span className="text-xs text-slate-500">
                    {m.played_at && new Date(m.played_at).toLocaleDateString("hu-HU")}
                    {m.play_log && m.play_log.length > 0 && (expanded ? " · bezár" : " · visszajátszás")}
                  </span>
                </button>
                <AnimatePresence>
                  {expanded && m.play_log && m.play_log.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25 }}
                      className="mt-3 overflow-hidden"
                    >
                      <MatchViewer
                        homeTeamName={m.home_team_name}
                        awayTeamName={m.away_team_name}
                        homeScore={m.home_score ?? 0}
                        awayScore={m.away_score ?? 0}
                        playLog={m.play_log}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
