import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { PlayEvent } from "../api/client";
import { useTeamTheme } from "../context/TeamThemeContext";
import PlayerAvatar from "./PlayerAvatar";
import AnimatedNumber from "./AnimatedNumber";

interface Props {
  homeTeamName: string;
  awayTeamName: string;
  homeScore: number;
  awayScore: number;
  playEvents: PlayEvent[];
}

// Playing field maps yard 0-100 onto this horizontal band; the remainder on
// each side is end zone. Two fixed vertical "lanes" give a pass its arc
// (passer stays put, target sits at a different lane) without needing real
// per-player lateral positioning.
const FIELD_START = 8;
const FIELD_END = 92;
const PRIMARY_LANE = 66;
const SECONDARY_LANE = 26;

const STEP_MS = 1900;
const REVEAL_DELAY_MS = 1050;

function yardToLeft(yard: number): number {
  return FIELD_START + (yard / 100) * (FIELD_END - FIELD_START);
}

export default function FieldView({ homeTeamName, awayTeamName, homeScore, awayScore, playEvents }: Props) {
  const { primary } = useTeamTheme();
  const [index, setIndex] = useState(0);
  const [revealResult, setRevealResult] = useState(false);
  const [burst, setBurst] = useState<string | null>(null);

  useEffect(() => {
    setIndex(0);
    setRevealResult(false);
    setBurst(null);
  }, [playEvents]);

  useEffect(() => {
    if (index >= playEvents.length) return;
    setRevealResult(false);
    const revealTimer = setTimeout(() => {
      setRevealResult(true);
      const ev = playEvents[index];
      if (ev.result === "touchdown") {
        setBurst(`TOUCHDOWN! ${ev.offense === "home" ? homeTeamName : awayTeamName}`);
        setTimeout(() => setBurst(null), 1100);
      }
    }, REVEAL_DELAY_MS);
    const advanceTimer = setTimeout(() => setIndex((i) => i + 1), STEP_MS);
    return () => {
      clearTimeout(revealTimer);
      clearTimeout(advanceTimer);
    };
  }, [index, playEvents, homeTeamName, awayTeamName]);

  const done = index >= playEvents.length;
  const current = !done ? playEvents[index] : null;

  const priorPlays = playEvents.slice(0, index);
  const runningHome = priorPlays.filter((p) => p.offense === "home").reduce((sum, p) => sum + p.points, 0);
  const runningAway = priorPlays.filter((p) => p.offense === "away").reduce((sum, p) => sum + p.points, 0);
  const currentQuarter = current?.quarter ?? playEvents[playEvents.length - 1]?.quarter ?? 1;

  const startLeft = current ? yardToLeft(current.start_yard) : 50;
  const endLeft = current ? yardToLeft(current.end_yard) : 50;
  const isPass = current?.play_type === "pass";
  const isRun = current?.play_type === "run";

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-950 p-4">
      <AnimatePresence>
        {burst && (
          <motion.div
            initial={{ opacity: 0, scale: 0.4 }}
            animate={{ opacity: 1, scale: 1.15 }}
            exit={{ opacity: 0, scale: 1.4 }}
            transition={{ duration: 0.35 }}
            className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center bg-black/50"
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
        <div className="px-3 text-xs text-slate-500">{done ? "VÉGE" : `${currentQuarter}. negyed`}</div>
        <div className="flex-1 text-center">
          <div className="truncate text-sm font-semibold text-slate-300">{awayTeamName}</div>
          <div className="text-3xl font-black text-white">
            <AnimatedNumber value={done ? awayScore : runningAway} />
          </div>
        </div>
      </div>

      {!done && (
        <button
          onClick={() => setIndex(playEvents.length)}
          className="mb-2 text-xs text-slate-500 underline hover:text-gridiron-accent"
        >
          Előretekerés a végére
        </button>
      )}

      <div className="relative mb-3 h-40 overflow-hidden rounded-lg border border-white/10" style={{ perspective: "700px" }}>
        {/* Turf layer -- the only part that gets the isometric-style tilt.
            Player tokens/labels live in a separate, flat overlay below so
            they stay crisp instead of fighting the 3D transform's
            perspective math (a deliberate, stylized simplification, not a
            precise projection). */}
        <div
          className="absolute inset-0"
          style={{
            transform: "rotateX(26deg)",
            transformOrigin: "bottom",
            background: "linear-gradient(180deg, #1f6b3a 0%, #175e32 60%, #124a28 100%)",
          }}
        >
          <div
            className="absolute inset-y-0 left-0"
            style={{ width: `${FIELD_START}%`, backgroundColor: primary, opacity: 0.5 }}
          />
          <div
            className="absolute inset-y-0 right-0"
            style={{ width: `${100 - FIELD_END}%`, backgroundColor: "#334155", opacity: 0.65 }}
          />
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "repeating-linear-gradient(90deg, rgba(255,255,255,0.35) 0px, rgba(255,255,255,0.35) 1px, transparent 1px, transparent 8.4%)",
            }}
          />
        </div>

        <div className="absolute inset-0">
          {current && (
            <>
              {isPass && (
                <svg className="absolute inset-0 h-full w-full">
                  <motion.line
                    x1={`${startLeft}%`}
                    y1={`${PRIMARY_LANE}%`}
                    initial={{ x2: `${startLeft}%`, y2: `${PRIMARY_LANE}%`, opacity: 0 }}
                    animate={{
                      x2: `${revealResult ? endLeft : startLeft}%`,
                      y2: `${revealResult ? SECONDARY_LANE : PRIMARY_LANE}%`,
                      opacity: revealResult ? 1 : 0,
                    }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    stroke="#facc15"
                    strokeWidth={2}
                    strokeDasharray="6 4"
                  />
                </svg>
              )}

              {current.primary_player && !isRun && (
                <div
                  className="absolute -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${startLeft}%`, top: `${PRIMARY_LANE}%` }}
                >
                  <PlayerAvatar
                    firstName={current.primary_player.first_name}
                    lastName={current.primary_player.last_name}
                    photoUrl={current.primary_player.photo_url}
                    size={32}
                  />
                </div>
              )}

              {isRun && current.primary_player && (
                <motion.div
                  className="absolute -translate-y-1/2"
                  style={{ top: `${PRIMARY_LANE}%`, translateX: "-50%" }}
                  initial={{ left: `${startLeft}%` }}
                  animate={{ left: `${revealResult ? endLeft : startLeft}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                >
                  <PlayerAvatar
                    firstName={current.primary_player.first_name}
                    lastName={current.primary_player.last_name}
                    photoUrl={current.primary_player.photo_url}
                    size={32}
                  />
                </motion.div>
              )}

              {isPass && revealResult && (
                <div
                  className="absolute -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${endLeft}%`, top: `${SECONDARY_LANE}%` }}
                >
                  {current.success && current.secondary_player ? (
                    <motion.div initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                      <PlayerAvatar
                        firstName={current.secondary_player.first_name}
                        lastName={current.secondary_player.last_name}
                        photoUrl={current.secondary_player.photo_url}
                        size={32}
                      />
                    </motion.div>
                  ) : (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1.3 }}
                      transition={{ type: "spring", stiffness: 400, damping: 12 }}
                      className="text-3xl font-black text-red-500 drop-shadow-[0_0_6px_rgba(239,68,68,0.8)]"
                    >
                      X
                    </motion.span>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {current && (
          <motion.p
            key={index}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center text-sm text-slate-300"
          >
            {current.text}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
