import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Pause, Play as PlayIcon, SkipBack, SkipForward } from "lucide-react";
import { PlayEvent } from "../api/client";
import AnimatedNumber from "./AnimatedNumber";
import PlayerAvatar from "./PlayerAvatar";
import { PrimaryButton, SecondaryButton } from "./ui";

interface MatchViewerProps {
  homeTeamName: string;
  awayTeamName: string;
  homeScore: number;
  awayScore: number;
  playLog: string[];
  playEvents?: PlayEvent[] | null;
  homeLogoUrl?: string | null;
  awayLogoUrl?: string | null;
  homePrimaryColor?: string | null;
  awayPrimaryColor?: string | null;
  /** Auto-advances with no manual controls, like watching it happen; false
   * (the default) shows Play/Pause/Next/Prev so a past match can be browsed. */
  isLive?: boolean;
}

// --- small, self-contained helpers -----------------------------------

const DOWN_LABELS = ["1st", "2nd", "3rd", "4th"];

function downLabel(down: number | null | undefined): string | null {
  if (!down) return null;
  return DOWN_LABELS[Math.min(Math.max(down, 1), 4) - 1];
}

/** 0-100 yard scale (0 = home's own goal line, 100 = away's) rendered the
 * way a broadcast reads it: relative to whichever half of the field it's on. */
function fieldPositionLabel(yard: number, homeAbbr: string, awayAbbr: string): string {
  if (yard === 50) return "50";
  if (yard < 50) return `${homeAbbr} ${yard}`;
  return `${awayAbbr} ${100 - yard}`;
}

function teamAbbr(name: string): string {
  const words = name.trim().split(/\s+/);
  const last = words[words.length - 1] ?? name;
  return last.slice(0, 3).toUpperCase();
}

function playHeadline(ev: PlayEvent): string {
  if (ev.result === "touchdown") {
    if (ev.play_type === "pass") return `${ev.yards}-yd Passing TD`;
    if (ev.play_type === "run") return `${ev.yards}-yd Rushing TD`;
    return "Touchdown";
  }
  if (ev.result === "field_goal") return `${ev.yards}-yd Field Goal`;
  if (ev.result === "safety") return "Safety";
  if (ev.play_type === "punt") return "Punt";
  if (ev.play_type === "pass") return ev.success ? `${ev.yards}-yd Pass` : "Incomplete Pass";
  if (ev.play_type === "run") return `${ev.yards}-yd Run`;
  return "Play";
}

// --- field geometry (0-100 yard scale mapped onto the visible band) ---

const FIELD_START = 6;
const FIELD_END = 94;
const PRIMARY_LANE = 68;
const SECONDARY_LANE = 22;
const STEP_MS = 2600;
const REVEAL_DELAY_MS = 1300;

function yardToLeft(yard: number): number {
  return FIELD_START + (yard / 100) * (FIELD_END - FIELD_START);
}

// --- confetti (TD celebration, no external library) --------------------

function Confetti({ color }: { color: string }) {
  const pieces = useMemo(
    () =>
      Array.from({ length: 28 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.35,
        duration: 1.5 + Math.random() * 0.9,
        rotate: (Math.random() - 0.5) * 540,
        color: Math.random() < 0.5 ? color : "#facc15",
      })),
    [color]
  );

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {pieces.map((p) => (
        <motion.span
          key={p.id}
          className="absolute top-0 h-2.5 w-1.5 rounded-sm"
          style={{ left: `${p.left}%`, backgroundColor: p.color }}
          initial={{ y: "-10%", opacity: 1, rotate: 0 }}
          animate={{ y: "130%", opacity: [1, 1, 0], rotate: p.rotate }}
          transition={{ duration: p.duration, delay: p.delay, ease: "easeIn" }}
        />
      ))}
    </div>
  );
}

// --- scoreboard ----------------------------------------------------------

function TimeoutTicks({ remaining, align }: { remaining: number | null; align: "left" | "right" }) {
  if (remaining === null) return null;
  return (
    <div className={`mt-1 flex gap-1 ${align === "right" ? "flex-row-reverse" : ""}`}>
      {[0, 1, 2].map((i) => (
        <span key={i} className={`h-1 w-4 rounded-full ${i < remaining ? "bg-amber-400" : "bg-white/15"}`} />
      ))}
    </div>
  );
}

function TeamBlock({
  abbr,
  logoUrl,
  score,
  align,
  hasBall,
  timeouts,
}: {
  abbr: string;
  logoUrl: string | null;
  score: number;
  align: "left" | "right";
  hasBall: boolean;
  timeouts: number | null;
}) {
  return (
    <div className={`flex min-w-0 flex-1 items-center gap-2.5 ${align === "right" ? "flex-row-reverse text-right" : "text-left"}`}>
      <PlayerAvatar firstName={abbr} lastName="" photoUrl={logoUrl} size={40} />
      <div className="min-w-0">
        <div className={`flex items-center gap-1.5 ${align === "right" ? "flex-row-reverse" : ""}`}>
          {hasBall && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />}
          <span className="truncate text-xs font-bold uppercase tracking-wider text-slate-300">{abbr}</span>
        </div>
        <div className="font-stat text-3xl font-black leading-tight text-white sm:text-4xl">
          <AnimatedNumber value={score} />
        </div>
        <TimeoutTicks remaining={timeouts} align={align} />
      </div>
    </div>
  );
}

function Scoreboard({
  homeAbbr,
  awayAbbr,
  homeLogoUrl,
  awayLogoUrl,
  homeColor,
  awayColor,
  homeScore,
  awayScore,
  quarter,
  clock,
  down,
  distance,
  possession,
  homeTimeouts,
  awayTimeouts,
  fieldPosLabel,
  final,
}: {
  homeAbbr: string;
  awayAbbr: string;
  homeLogoUrl: string | null;
  awayLogoUrl: string | null;
  homeColor: string;
  awayColor: string;
  homeScore: number;
  awayScore: number;
  quarter: number;
  clock: string | null;
  down: number | null;
  distance: number | null;
  possession: "home" | "away" | null;
  homeTimeouts: number | null;
  awayTimeouts: number | null;
  fieldPosLabel: string | null;
  final: boolean;
}) {
  return (
    <div
      className="relative overflow-hidden px-4 py-4 sm:px-6"
      style={{ background: `linear-gradient(90deg, ${homeColor}66 0%, #04060b 46%, #04060b 54%, ${awayColor}66 100%)` }}
    >
      <div className="absolute inset-0 bg-slate-950/35" />
      <div className="relative flex items-center justify-between gap-2">
        <TeamBlock abbr={homeAbbr} logoUrl={homeLogoUrl} score={homeScore} align="left" hasBall={possession === "home"} timeouts={homeTimeouts} />

        <div className="flex shrink-0 flex-col items-center px-2 text-center">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            {final ? "Vége" : `${quarter}. negyed`}
          </span>
          {!final && <span className="font-stat text-lg font-black text-white">{clock ?? "--:--"}</span>}
          {!final && down && distance && (
            <span className="mt-1 whitespace-nowrap rounded bg-white/10 px-2 py-0.5 text-[11px] font-semibold text-slate-200">
              {downLabel(down)} & {distance}
              {fieldPosLabel && <> &middot; {fieldPosLabel}</>}
            </span>
          )}
        </div>

        <TeamBlock abbr={awayAbbr} logoUrl={awayLogoUrl} score={awayScore} align="right" hasBall={possession === "away"} timeouts={awayTimeouts} />
      </div>
    </div>
  );
}

// --- animated field --------------------------------------------------

function Field({
  event,
  revealResult,
  homeColor,
  awayColor,
  homeAbbr,
  awayAbbr,
}: {
  event: PlayEvent | null;
  revealResult: boolean;
  homeColor: string;
  awayColor: string;
  homeAbbr: string;
  awayAbbr: string;
}) {
  const startLeft = event ? yardToLeft(event.start_yard) : 50;
  const endLeft = event ? yardToLeft(event.end_yard) : 50;
  const isPass = event?.play_type === "pass";
  const isRun = event?.play_type === "run";
  const isKick = event?.play_type === "field_goal" || event?.play_type === "punt";
  const direction = event?.offense === "home" ? 1 : -1;
  const firstDownYard =
    event && event.down && event.distance
      ? Math.max(0, Math.min(100, event.start_yard + direction * event.distance))
      : null;

  return (
    <div className="relative h-48 overflow-hidden border-y border-white/10 sm:h-60" style={{ perspective: "900px" }}>
      {/* Turf layer -- the only part with the "isometric-ish" tilt. Player
          tokens/lines live in a separate flat overlay below so they stay
          crisp instead of fighting the 3D transform's perspective math (a
          deliberate stylization, not a precise projection). */}
      <div
        className="absolute inset-0"
        style={{
          transform: "rotateX(22deg)",
          transformOrigin: "bottom",
          background: "linear-gradient(180deg,#1b6236 0%,#155129 55%,#0f3f20 100%)",
        }}
      >
        <div
          className="absolute inset-y-0 left-0 flex items-center justify-center"
          style={{ width: `${FIELD_START}%`, backgroundColor: homeColor, opacity: 0.55 }}
        >
          <span className="text-[10px] font-black tracking-widest text-white/85 [writing-mode:vertical-rl]">{homeAbbr}</span>
        </div>
        <div
          className="absolute inset-y-0 right-0 flex items-center justify-center"
          style={{ width: `${100 - FIELD_END}%`, backgroundColor: awayColor, opacity: 0.55 }}
        >
          <span className="rotate-180 text-[10px] font-black tracking-widest text-white/85 [writing-mode:vertical-rl]">{awayAbbr}</span>
        </div>
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(255,255,255,0.35) 0px, rgba(255,255,255,0.35) 1px, transparent 1px, transparent 8.8%)",
          }}
        />
        <div className="absolute inset-y-0 w-px bg-white/50" style={{ left: "50%" }} />
      </div>

      <div className="absolute inset-0">
        {event && (
          <>
            <div className="absolute inset-y-0 w-0.5 bg-sky-400/70" style={{ left: `${startLeft}%` }} />
            {firstDownYard !== null && (
              <div className="absolute inset-y-0 w-0.5 bg-yellow-400/80" style={{ left: `${yardToLeft(firstDownYard)}%` }} />
            )}

            {isPass && (
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
                <motion.line
                  x1={startLeft}
                  y1={PRIMARY_LANE}
                  initial={{ x2: startLeft, y2: PRIMARY_LANE, opacity: 0 }}
                  animate={{
                    x2: revealResult ? endLeft : startLeft,
                    y2: revealResult ? SECONDARY_LANE : PRIMARY_LANE,
                    opacity: revealResult ? 1 : 0,
                  }}
                  transition={{ duration: 0.55, ease: "easeOut" }}
                  stroke="#facc15"
                  strokeWidth={2.2}
                  strokeDasharray="7 5"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            )}

            {isRun && (
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
                <motion.line
                  x1={startLeft}
                  y1={PRIMARY_LANE}
                  y2={PRIMARY_LANE}
                  initial={{ x2: startLeft }}
                  animate={{ x2: revealResult ? endLeft : startLeft }}
                  transition={{ duration: 0.9, ease: "easeOut" }}
                  stroke="#38bdf8"
                  strokeWidth={2.2}
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            )}

            {isKick && (
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
                <motion.path
                  d={`M ${startLeft} 78 Q ${(startLeft + endLeft) / 2} 6, ${endLeft} 78`}
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth={2}
                  strokeDasharray="1.4 2.2"
                  vectorEffect="non-scaling-stroke"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: revealResult ? 1 : 0, opacity: revealResult ? 1 : 0 }}
                  transition={{ duration: 0.9, ease: "easeOut" }}
                />
              </svg>
            )}

            {event.primary_player && !isRun && (
              <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${startLeft}%`, top: `${PRIMARY_LANE}%` }}>
                <PlayerAvatar
                  firstName={event.primary_player.first_name}
                  lastName={event.primary_player.last_name}
                  photoUrl={event.primary_player.photo_url}
                  size={32}
                />
              </div>
            )}

            {isRun && event.primary_player && (
              <motion.div
                className="absolute -translate-y-1/2"
                style={{ top: `${PRIMARY_LANE}%`, translateX: "-50%" }}
                initial={{ left: `${startLeft}%` }}
                animate={{ left: `${revealResult ? endLeft : startLeft}%` }}
                transition={{ duration: 0.9, ease: "easeOut" }}
              >
                <PlayerAvatar
                  firstName={event.primary_player.first_name}
                  lastName={event.primary_player.last_name}
                  photoUrl={event.primary_player.photo_url}
                  size={32}
                />
              </motion.div>
            )}

            {isPass && revealResult && (
              <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${endLeft}%`, top: `${SECONDARY_LANE}%` }}>
                {event.success && event.secondary_player ? (
                  <motion.div initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                    <PlayerAvatar
                      firstName={event.secondary_player.first_name}
                      lastName={event.secondary_player.last_name}
                      photoUrl={event.secondary_player.photo_url}
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
  );
}

// --- last play bar -----------------------------------------------------

function LastPlayBar({ event }: { event: PlayEvent | null }) {
  if (!event) {
    return <div className="border-b border-white/10 bg-black/30 px-4 py-2 text-xs text-slate-500 sm:px-6">Kezdés...</div>;
  }
  return (
    <div className="border-b border-white/10 bg-black/30 px-4 py-2 sm:px-6">
      <div className="text-[11px] font-bold uppercase tracking-wide text-amber-400">{playHeadline(event)}</div>
      <div className="text-xs text-slate-300">{event.text}</div>
    </div>
  );
}

// --- playback controls (replay mode only) -------------------------------

function PlaybackControls({
  playing,
  onTogglePlay,
  onPrev,
  onNext,
  disabledPrev,
  disabledNext,
}: {
  playing: boolean;
  onTogglePlay: () => void;
  onPrev: () => void;
  onNext: () => void;
  disabledPrev: boolean;
  disabledNext: boolean;
}) {
  return (
    <div className="flex items-center justify-center gap-3 border-b border-white/10 bg-black/20 px-4 py-2">
      <SecondaryButton onClick={onPrev} disabled={disabledPrev} className="px-2 py-1.5" aria-label="Előző játék">
        <SkipBack size={14} />
      </SecondaryButton>
      <PrimaryButton onClick={onTogglePlay} className="px-4 py-1.5" aria-label={playing ? "Szünet" : "Lejátszás"}>
        {playing ? <Pause size={14} /> : <PlayIcon size={14} />}
      </PrimaryButton>
      <SecondaryButton onClick={onNext} disabled={disabledNext} className="px-2 py-1.5" aria-label="Következő játék">
        <SkipForward size={14} />
      </SecondaryButton>
    </div>
  );
}

// --- tabs: legújabb / statisztikák / játékok ----------------------------

type TabKey = "latest" | "stats" | "plays";

function Tabs({ active, onChange }: { active: TabKey; onChange: (tab: TabKey) => void }) {
  const items: { key: TabKey; label: string }[] = [
    { key: "latest", label: "Legújabb" },
    { key: "stats", label: "Statisztikák" },
    { key: "plays", label: "Játékok" },
  ];
  return (
    <div className="flex border-b border-white/10">
      {items.map((it) => (
        <button
          key={it.key}
          onClick={() => onChange(it.key)}
          className={`flex-1 px-3 py-2 text-xs font-semibold uppercase tracking-wide transition ${
            active === it.key ? "border-b-2 border-team-primary text-white" : "text-slate-500 hover:text-slate-300"
          }`}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

function LatestPanel({ plays }: { plays: PlayEvent[] }) {
  const recent = useMemo(() => [...plays].reverse().slice(0, 6), [plays]);
  if (recent.length === 0) return <p className="p-4 text-sm text-slate-500">Még nem történt játék.</p>;
  return (
    <div className="max-h-64 space-y-2 overflow-y-auto p-3">
      {recent.map((ev, i) => (
        <div key={i} className="rounded-lg bg-white/5 px-3 py-2 text-xs">
          <div className="font-bold text-slate-100">{playHeadline(ev)}</div>
          <div className="text-slate-400">{ev.text}</div>
        </div>
      ))}
    </div>
  );
}

function PlaysPanel({ plays, onJump }: { plays: PlayEvent[]; onJump: (index: number) => void }) {
  const byQuarter = useMemo(() => {
    const groups = new Map<number, { ev: PlayEvent; idx: number }[]>();
    plays.forEach((ev, idx) => {
      const list = groups.get(ev.quarter) ?? [];
      list.push({ ev, idx });
      groups.set(ev.quarter, list);
    });
    return [...groups.entries()].sort((a, b) => a[0] - b[0]);
  }, [plays]);

  if (plays.length === 0) return <p className="p-4 text-sm text-slate-500">Még nem történt játék.</p>;

  return (
    <div className="max-h-72 space-y-4 overflow-y-auto p-3">
      {byQuarter.map(([q, items]) => (
        <div key={q}>
          <div className="mb-1.5 text-[11px] font-bold uppercase tracking-widest text-slate-500">{q}. negyed</div>
          <div className="space-y-1.5">
            {items.map(({ ev, idx }) => (
              <button
                key={idx}
                onClick={() => onJump(idx)}
                className="block w-full rounded-lg bg-white/5 px-3 py-2 text-left text-xs transition hover:bg-white/10"
              >
                {(ev.down || ev.clock) && (
                  <div className="mb-0.5 text-slate-500">
                    {ev.down && ev.distance ? `${downLabel(ev.down)} & ${ev.distance}` : ""}
                    {ev.down && ev.clock ? " · " : ""}
                    {ev.clock ?? ""}
                  </div>
                )}
                <div className="font-bold text-slate-100">{playHeadline(ev)}</div>
                <div className="mt-1 flex items-center gap-1.5 text-slate-400">
                  {ev.primary_player && (
                    <PlayerAvatar
                      firstName={ev.primary_player.first_name}
                      lastName={ev.primary_player.last_name}
                      photoUrl={ev.primary_player.photo_url}
                      size={18}
                    />
                  )}
                  {ev.secondary_player && (
                    <PlayerAvatar
                      firstName={ev.secondary_player.first_name}
                      lastName={ev.secondary_player.last_name}
                      photoUrl={ev.secondary_player.photo_url}
                      size={18}
                    />
                  )}
                  <span>{ev.text}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// --- stats tab: real box-score numbers computed from the plays seen so far

interface StatRow {
  name: string;
  photoUrl: string | null;
  line: string;
  yards: number;
}

function computeTeamStats(plays: PlayEvent[], side: "home" | "away") {
  const passing = new Map<string, { photoUrl: string | null; att: number; comp: number; yards: number; td: number }>();
  const rushing = new Map<string, { photoUrl: string | null; att: number; yards: number; td: number }>();
  const receiving = new Map<string, { photoUrl: string | null; rec: number; yards: number; td: number }>();

  for (const ev of plays) {
    if (ev.offense !== side) continue;

    if (ev.play_type === "pass" && ev.primary_player) {
      const key = `${ev.primary_player.first_name} ${ev.primary_player.last_name}`;
      const row = passing.get(key) ?? { photoUrl: ev.primary_player.photo_url, att: 0, comp: 0, yards: 0, td: 0 };
      row.att += 1;
      if (ev.success) row.comp += 1;
      row.yards += ev.yards;
      if (ev.result === "touchdown") row.td += 1;
      passing.set(key, row);

      if (ev.success && ev.secondary_player) {
        const rk = `${ev.secondary_player.first_name} ${ev.secondary_player.last_name}`;
        const rrow = receiving.get(rk) ?? { photoUrl: ev.secondary_player.photo_url, rec: 0, yards: 0, td: 0 };
        rrow.rec += 1;
        rrow.yards += ev.yards;
        if (ev.result === "touchdown") rrow.td += 1;
        receiving.set(rk, rrow);
      }
    } else if (ev.play_type === "run" && ev.primary_player) {
      const key = `${ev.primary_player.first_name} ${ev.primary_player.last_name}`;
      const row = rushing.get(key) ?? { photoUrl: ev.primary_player.photo_url, att: 0, yards: 0, td: 0 };
      row.att += 1;
      row.yards += ev.yards;
      if (ev.result === "touchdown") row.td += 1;
      rushing.set(key, row);
    }
  }

  const toRows = <T extends { photoUrl: string | null; yards: number; td: number }>(
    map: Map<string, T>,
    format: (name: string, row: T) => string
  ): StatRow[] =>
    [...map.entries()]
      .sort((a, b) => b[1].yards - a[1].yards)
      .map(([name, row]) => ({ name, photoUrl: row.photoUrl, yards: row.yards, line: format(name, row) }));

  return {
    passing: toRows(passing, (_, r) => `${r.comp}/${r.att}, ${r.yards} yd${r.td ? `, ${r.td} TD` : ""}`),
    rushing: toRows(rushing, (_, r) => `${r.att} futás, ${r.yards} yd${r.td ? `, ${r.td} TD` : ""}`),
    receiving: toRows(receiving, (_, r) => `${r.rec} elkapás, ${r.yards} yd${r.td ? `, ${r.td} TD` : ""}`),
  };
}

function StatTable({ title, rows }: { title: string; rows: StatRow[] }) {
  if (rows.length === 0) return null;
  return (
    <div className="mb-2.5">
      <div className="mb-1 text-[10px] uppercase tracking-wide text-slate-600">{title}</div>
      <div className="space-y-1">
        {rows.map((r) => {
          const [first, ...rest] = r.name.split(" ");
          return (
            <div key={r.name} className="flex items-center gap-2">
              <PlayerAvatar firstName={first} lastName={rest.join(" ")} photoUrl={r.photoUrl} size={20} />
              <span className="flex-1 truncate text-slate-200">{r.name}</span>
              <span className="shrink-0 text-slate-400">{r.line}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatsPanel({ plays, homeTeamName, awayTeamName }: { plays: PlayEvent[]; homeTeamName: string; awayTeamName: string }) {
  const home = useMemo(() => computeTeamStats(plays, "home"), [plays]);
  const away = useMemo(() => computeTeamStats(plays, "away"), [plays]);

  if (plays.length === 0) return <p className="p-4 text-sm text-slate-500">Még nincs statisztika.</p>;

  return (
    <div className="max-h-72 space-y-4 overflow-y-auto p-3 text-xs">
      {[
        { label: homeTeamName, stats: home },
        { label: awayTeamName, stats: away },
      ].map(({ label, stats }) =>
        stats.passing.length || stats.rushing.length || stats.receiving.length ? (
          <div key={label}>
            <div className="mb-1.5 text-[11px] font-bold uppercase tracking-widest text-slate-500">{label}</div>
            <StatTable title="Passzjátékosok" rows={stats.passing} />
            <StatTable title="Futójátékosok" rows={stats.rushing} />
            <StatTable title="Elkapójátékosok" rows={stats.receiving} />
          </div>
        ) : null
      )}
    </div>
  );
}

// --- the broadcast-style viewer (used whenever structured play data exists)

function BroadcastViewer({
  homeTeamName,
  awayTeamName,
  homeScore,
  awayScore,
  plays,
  isLive,
  homeLogoUrl,
  awayLogoUrl,
  homeColor,
  awayColor,
}: {
  homeTeamName: string;
  awayTeamName: string;
  homeScore: number;
  awayScore: number;
  plays: PlayEvent[];
  isLive: boolean;
  homeLogoUrl: string | null;
  awayLogoUrl: string | null;
  homeColor: string;
  awayColor: string;
}) {
  const homeAbbr = useMemo(() => teamAbbr(homeTeamName), [homeTeamName]);
  const awayAbbr = useMemo(() => teamAbbr(awayTeamName), [awayTeamName]);

  const [index, setIndex] = useState(0);
  const [revealResult, setRevealResult] = useState(false);
  const [playing, setPlaying] = useState(isLive);
  const [tdBanner, setTdBanner] = useState<string | null>(null);
  const [tab, setTab] = useState<TabKey>("plays");

  useEffect(() => {
    setIndex(0);
    setRevealResult(false);
    setPlaying(isLive);
    setTdBanner(null);
  }, [plays, isLive]);

  useEffect(() => {
    if (!playing) return;
    if (index >= plays.length) {
      setPlaying(false);
      return;
    }
    setRevealResult(false);
    const revealTimer = setTimeout(() => {
      setRevealResult(true);
      const ev = plays[index];
      if (ev.result === "touchdown") {
        setTdBanner(ev.offense === "home" ? homeTeamName : awayTeamName);
        setTimeout(() => setTdBanner(null), 1700);
      }
    }, REVEAL_DELAY_MS);
    const advanceTimer = setTimeout(() => setIndex((i) => i + 1), STEP_MS);
    return () => {
      clearTimeout(revealTimer);
      clearTimeout(advanceTimer);
    };
  }, [playing, index, plays, homeTeamName, awayTeamName]);

  const done = index >= plays.length;
  const current = !done ? plays[index] : null;

  const visiblePlays = useMemo(() => {
    if (done) return plays;
    return revealResult ? plays.slice(0, index + 1) : plays.slice(0, index);
  }, [plays, index, revealResult, done]);

  const runningHome = visiblePlays.filter((p) => p.offense === "home").reduce((sum, p) => sum + p.points, 0);
  const runningAway = visiblePlays.filter((p) => p.offense === "away").reduce((sum, p) => sum + p.points, 0);
  const lastPlay = visiblePlays.length > 0 ? visiblePlays[visiblePlays.length - 1] : null;
  const fieldPosLabel = current ? fieldPositionLabel(current.start_yard, homeAbbr, awayAbbr) : null;

  function jumpTo(i: number) {
    setPlaying(false);
    setIndex(i);
    setRevealResult(true);
  }
  function goNext() {
    setPlaying(false);
    setIndex((i) => Math.min(i + 1, plays.length));
    setRevealResult(true);
  }
  function goPrev() {
    setPlaying(false);
    setIndex((i) => Math.max(i - 1, 0));
    setRevealResult(true);
  }
  function togglePlay() {
    if (done) {
      setIndex(0);
      setRevealResult(false);
      setPlaying(true);
      return;
    }
    setPlaying((p) => !p);
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950 shadow-lg">
      <Scoreboard
        homeAbbr={homeAbbr}
        awayAbbr={awayAbbr}
        homeLogoUrl={homeLogoUrl}
        awayLogoUrl={awayLogoUrl}
        homeColor={homeColor}
        awayColor={awayColor}
        homeScore={done ? homeScore : runningHome}
        awayScore={done ? awayScore : runningAway}
        quarter={current?.quarter ?? plays[plays.length - 1]?.quarter ?? 1}
        clock={current?.clock ?? null}
        down={current?.down ?? null}
        distance={current?.distance ?? null}
        possession={current?.offense ?? null}
        homeTimeouts={current?.home_timeouts ?? null}
        awayTimeouts={current?.away_timeouts ?? null}
        fieldPosLabel={fieldPosLabel}
        final={done}
      />

      {!isLive && (
        <PlaybackControls
          playing={playing}
          onTogglePlay={togglePlay}
          onPrev={goPrev}
          onNext={goNext}
          disabledPrev={index === 0}
          disabledNext={done}
        />
      )}

      <div className="relative">
        <Field event={current} revealResult={revealResult} homeColor={homeColor} awayColor={awayColor} homeAbbr={homeAbbr} awayAbbr={awayAbbr} />
        <AnimatePresence>
          {tdBanner && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="pointer-events-none absolute inset-0 z-30 flex items-center justify-center bg-black/60"
            >
              <Confetti color={tdBanner === homeTeamName ? homeColor : awayColor} />
              <motion.span
                initial={{ scale: 0.5, opacity: 0, rotate: -6 }}
                animate={{ scale: 1.08, opacity: 1, rotate: 0 }}
                exit={{ scale: 1.3, opacity: 0 }}
                transition={{ type: "spring", stiffness: 260, damping: 16 }}
                className="px-4 text-center text-5xl font-black uppercase tracking-wider text-yellow-300 drop-shadow-[0_0_30px_rgba(250,204,21,0.9)] sm:text-6xl"
              >
                Touchdown!
              </motion.span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <LastPlayBar event={lastPlay} />

      <Tabs active={tab} onChange={setTab} />
      {tab === "latest" && <LatestPanel plays={visiblePlays} />}
      {tab === "stats" && <StatsPanel plays={visiblePlays} homeTeamName={homeTeamName} awayTeamName={awayTeamName} />}
      {tab === "plays" && <PlaysPanel plays={visiblePlays} onJump={jumpTo} />}
    </div>
  );
}

// --- legacy fallback: classic text log (matches predating play_events) ---

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

function ClassicTextLog({
  homeTeamName,
  awayTeamName,
  homeScore,
  awayScore,
  playLog,
}: {
  homeTeamName: string;
  awayTeamName: string;
  homeScore: number;
  awayScore: number;
  playLog: string[];
}) {
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
  const runningHome = parsed.slice(0, revealed).filter((p) => p.team === homeTeamName).reduce((sum, p) => sum + p.points, 0);
  const runningAway = parsed.slice(0, revealed).filter((p) => p.team === awayTeamName).reduce((sum, p) => sum + p.points, 0);
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

// --- public entry point --------------------------------------------------

export default function MatchViewer({
  homeTeamName,
  awayTeamName,
  homeScore,
  awayScore,
  playLog,
  playEvents,
  homeLogoUrl = null,
  awayLogoUrl = null,
  homePrimaryColor = null,
  awayPrimaryColor = null,
  isLive = false,
}: MatchViewerProps) {
  const hasStructuredPlays = !!playEvents && playEvents.length > 0;

  if (!hasStructuredPlays) {
    return <ClassicTextLog homeTeamName={homeTeamName} awayTeamName={awayTeamName} homeScore={homeScore} awayScore={awayScore} playLog={playLog} />;
  }

  return (
    <BroadcastViewer
      homeTeamName={homeTeamName}
      awayTeamName={awayTeamName}
      homeScore={homeScore}
      awayScore={awayScore}
      plays={playEvents!}
      isLive={isLive}
      homeLogoUrl={homeLogoUrl}
      awayLogoUrl={awayLogoUrl}
      homeColor={homePrimaryColor ?? "#0ea5e9"}
      awayColor={awayPrimaryColor ?? "#64748b"}
    />
  );
}
