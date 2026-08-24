import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber";

interface Props {
  homeTeamName: string;
  awayTeamName: string;
  homeScore: number;
  awayScore: number;
  playLog: string[];
}

interface ParsedPlay {
  team: string | null;
  quarter: string | null;
  points: number;
  isTouchdown: boolean;
  text: string;
}

function parseLine(line: string): ParsedPlay {
  const teamMatch = line.match(/^\[(.+?)\]/);
  const quarterMatch = line.match(/(\d+)\.\s*negyed/);
  const pointsMatch = line.match(/\(\+(\d+)\)/);
  return {
    team: teamMatch?.[1] ?? null,
    quarter: quarterMatch?.[1] ?? null,
    points: pointsMatch ? Number(pointsMatch[1]) : 0,
    isTouchdown: line.includes("Touchdown"),
    text: line.replace(/^\[.+?\]\s*/, ""),
  };
}

export default function MatchViewer({ homeTeamName, awayTeamName, homeScore, awayScore, playLog }: Props) {
  const parsed = useMemo(() => playLog.map(parseLine), [playLog]);
  const [revealed, setRevealed] = useState(0);
  const [burst, setBurst] = useState<string | null>(null);

  useEffect(() => {
    setRevealed(0);
    setBurst(null);
  }, [playLog]);

  useEffect(() => {
    if (revealed >= parsed.length) return;
    const timer = setTimeout(() => {
      const next = parsed[revealed];
      if (next?.isTouchdown) {
        setBurst(`TOUCHDOWN! ${next.team ?? ""}`);
        setTimeout(() => setBurst(null), 1100);
      }
      setRevealed((r) => r + 1);
    }, 650);
    return () => clearTimeout(timer);
  }, [revealed, parsed]);

  const done = revealed >= parsed.length;

  const runningHome = parsed
    .slice(0, revealed)
    .filter((p) => p.team === homeTeamName)
    .reduce((sum, p) => sum + p.points, 0);
  const runningAway = parsed
    .slice(0, revealed)
    .filter((p) => p.team === awayTeamName)
    .reduce((sum, p) => sum + p.points, 0);

  const currentQuarter = revealed > 0 ? parsed[revealed - 1]?.quarter : null;

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950 p-4">
      <AnimatePresence>
        {burst && (
          <motion.div
            initial={{ opacity: 0, scale: 0.4 }}
            animate={{ opacity: 1, scale: 1.15 }}
            exit={{ opacity: 0, scale: 1.4 }}
            transition={{ duration: 0.35 }}
            className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-black/50"
          >
            <span className="px-4 text-center text-3xl font-black uppercase tracking-wider text-gridiron-accent drop-shadow-[0_0_14px_rgba(52,211,153,0.85)] sm:text-4xl">
              {burst}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mb-3 flex items-center justify-between">
        <div className="flex-1 text-center">
          <div className="truncate text-sm font-semibold text-slate-300">{homeTeamName}</div>
          <div className="text-3xl font-black text-white">
            <AnimatedNumber value={done ? homeScore : runningHome} />
          </div>
        </div>
        <div className="px-3 text-xs text-slate-500">
          {done ? "VÉGE" : currentQuarter ? `${currentQuarter}. negyed` : "Kezdés..."}
        </div>
        <div className="flex-1 text-center">
          <div className="truncate text-sm font-semibold text-slate-300">{awayTeamName}</div>
          <div className="text-3xl font-black text-white">
            <AnimatedNumber value={done ? awayScore : runningAway} />
          </div>
        </div>
      </div>

      {!done && (
        <button
          onClick={() => setRevealed(parsed.length)}
          className="mb-2 text-xs text-slate-500 underline hover:text-gridiron-accent"
        >
          Előretekerés a végére
        </button>
      )}

      <div className="max-h-56 space-y-1 overflow-y-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-400">
        <AnimatePresence initial={false}>
          {parsed.slice(0, revealed).map((p, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              className={p.isTouchdown ? "font-semibold text-gridiron-accent" : ""}
            >
              [{p.team}] {p.text}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
