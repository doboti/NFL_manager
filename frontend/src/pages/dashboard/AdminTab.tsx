import { useState } from "react";
import { motion } from "framer-motion";
import { AdvanceTimeResponse, Team, advanceTime, fetchMyTeam, resetTime } from "../../api/client";
import { useVirtualTime } from "../../context/TimeContext";

interface Props {
  onTeamUpdate?: (team: Team) => void;
}

const QUICK_JUMPS = [1, 6, 12, 24];

export default function AdminTab({ onTeamUpdate }: Props) {
  const { offsetSeconds, setOffsetSeconds, virtualNow } = useVirtualTime();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<AdvanceTimeResponse | null>(null);

  async function handleAdvance(hours: number) {
    setBusy(`advance-${hours}`);
    setError(null);
    try {
      const result = await advanceTime(hours);
      setOffsetSeconds(result.time.offset_seconds);
      setLastResult(result);
      // stadium level / capital may have changed via the daily cycle
      if (onTeamUpdate) onTeamUpdate(await fetchMyTeam());
    } catch {
      setError("Az idő előreléptetése nem sikerült.");
    } finally {
      setBusy(null);
    }
  }

  async function handleReset() {
    setBusy("reset");
    setError(null);
    try {
      const status = await resetTime();
      setOffsetSeconds(status.offset_seconds);
      setLastResult(null);
      if (onTeamUpdate) onTeamUpdate(await fetchMyTeam());
    } catch {
      setError("Az idő visszaállítása nem sikerült.");
    } finally {
      setBusy(null);
    }
  }

  const offsetHours = offsetSeconds / 3600;

  return (
    <div>
      <h2 className="mb-1 text-xl font-semibold">Admin / teszt óra</h2>
      <p className="mb-4 text-xs text-slate-500">
        Csak fejlesztési/tesztelési célra: előreléptet egy virtuális órát, amit minden edzés-, stadionfejlesztés-
        és meccsidőzítés figyelembe vesz. Ez rögtön lefuttatja a napi ciklust is, hogy az esedékes meccsek is
        lejátszódjanak.
      </p>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900 p-4">
        <div className="mb-1 text-sm text-slate-400">
          Eltolás: <span className="font-semibold text-gridiron-accent">{offsetHours.toFixed(1)} óra</span>
        </div>
        <div className="text-xs text-slate-500">Virtuális idő: {new Date(virtualNow()).toLocaleString("hu-HU")}</div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {QUICK_JUMPS.map((hours) => (
          <motion.button
            key={hours}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.96 }}
            disabled={busy !== null}
            onClick={() => handleAdvance(hours)}
            className="rounded-lg bg-gridiron-accent px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40"
          >
            {busy === `advance-${hours}` ? "..." : `+${hours} óra`}
          </motion.button>
        ))}
        <button
          disabled={busy !== null || offsetSeconds === 0}
          onClick={handleReset}
          className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 disabled:opacity-30"
        >
          {busy === "reset" ? "..." : "Idő visszaállítása"}
        </button>
      </div>

      {lastResult?.daily_cycle && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300">
          <div className="mb-2 font-semibold">Legutóbbi napi ciklus eredménye</div>
          <div className="text-xs text-slate-400">
            Lejátszott meccsek: {(lastResult.daily_cycle.matches as unknown[])?.length ?? 0}
          </div>
          <div className="text-xs text-slate-400">
            Szezonok: {JSON.stringify(lastResult.daily_cycle.seasons)}
          </div>
          {lastResult.daily_cycle.playoff_events &&
          Object.keys(lastResult.daily_cycle.playoff_events as object).length > 0 ? (
            <div className="text-xs text-gridiron-cyan">
              Rájátszás események: {JSON.stringify(lastResult.daily_cycle.playoff_events)}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
