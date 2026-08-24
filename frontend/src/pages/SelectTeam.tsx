import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { LeagueOption, NFLTeamOption, claimTeam, listAvailableLeagues, listAvailableTeams } from "../api/client";
import PageTransition from "../components/PageTransition";

type Step = "league" | "team";

export default function SelectTeam() {
  const [step, setStep] = useState<Step>("league");
  const [leagues, setLeagues] = useState<LeagueOption[]>([]);
  const [leaguesError, setLeaguesError] = useState<string | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<string | null>(null);
  const [teams, setTeams] = useState<NFLTeamOption[]>([]);
  const [teamsError, setTeamsError] = useState<string | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    listAvailableLeagues()
      .then((data) => {
        setLeagues(data);
        setSelectedLeague((prev) => prev ?? data[0]?.key ?? null);
      })
      .catch(() => setLeaguesError("Nem sikerült betölteni a ligalistát."));
  }, []);

  useEffect(() => {
    if (step !== "team" || !selectedLeague) return;
    setTeams([]);
    setSelectedCode(null);
    listAvailableTeams(selectedLeague)
      .then(setTeams)
      .catch(() => setTeamsError("Nem sikerült betölteni a csapatlistát."));
  }, [step, selectedLeague]);

  async function handleClaim() {
    if (!selectedCode || !selectedLeague) return;
    setError(null);
    setSubmitting(true);
    try {
      await claimTeam(selectedLeague, selectedCode);
      navigate("/");
    } catch {
      setError("Nem sikerült lefoglalni ezt a csapatot. Lehet, hogy időközben más választotta.");
      listAvailableTeams(selectedLeague).then(setTeams).catch(() => undefined);
    } finally {
      setSubmitting(false);
    }
  }

  const selectedTeam = teams.find((t) => t.code === selectedCode);

  return (
    <PageTransition>
      <div className="flex min-h-screen items-center justify-center px-4 py-10">
        <motion.div
          initial={{ scale: 0.96, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-8 shadow-xl"
        >
          <h1 className="text-2xl font-bold text-gridiron-accent">Válassz ligát és csapatot</h1>
          <p className="mb-6 text-sm text-slate-400">
            A kiválasztott csapat jelenleg szabad rosterének legjobb játékosait megkapod.
          </p>

          <div className="mb-6 flex items-center gap-2 text-xs text-slate-500">
            <span className={step === "league" ? "text-gridiron-accent" : ""}>1. Liga</span>
            <span>→</span>
            <span className={step === "team" ? "text-gridiron-accent" : ""}>2. Csapat</span>
          </div>

          <AnimatePresence mode="wait">
            {step === "league" && (
              <motion.div
                key="league"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                <label className="block text-sm text-slate-400">Liga</label>

                {leaguesError && <p className="text-sm text-red-400">{leaguesError}</p>}

                <select
                  value={selectedLeague ?? ""}
                  onChange={(e) => setSelectedLeague(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 outline-none focus:border-gridiron-accent"
                >
                  {leagues.map((l) => (
                    <option key={l.key} value={l.key}>
                      {l.name}
                    </option>
                  ))}
                </select>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  type="button"
                  disabled={!selectedLeague}
                  onClick={() => setStep("team")}
                  className="w-full rounded-lg bg-gridiron-accent py-2 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-40"
                >
                  Tovább
                </motion.button>
              </motion.div>
            )}

            {step === "team" && (
              <motion.div
                key="team"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                <label className="block text-sm text-slate-400">
                  Válassz csapatot ({leagues.find((l) => l.key === selectedLeague)?.name})
                </label>

                {teamsError && <p className="text-sm text-red-400">{teamsError}</p>}

                <div className="grid max-h-72 grid-cols-2 gap-2 overflow-y-auto pr-1 sm:grid-cols-3">
                  {teams.map((t) => (
                    <button
                      key={t.code}
                      type="button"
                      disabled={t.taken}
                      onClick={() => setSelectedCode(t.code)}
                      className={`rounded-lg border px-2 py-2 text-left text-xs transition ${
                        t.taken
                          ? "cursor-not-allowed border-slate-800 bg-slate-900 text-slate-600"
                          : selectedCode === t.code
                          ? "border-gridiron-accent bg-gridiron-accent/10 text-gridiron-accent"
                          : "border-slate-700 bg-slate-800 text-slate-300 hover:border-gridiron-accent"
                      }`}
                    >
                      <div className="font-semibold">{t.code}</div>
                      <div className="truncate">{t.taken ? "Foglalt" : t.name}</div>
                      {!t.taken && t.controlled_by_bot && (
                        <div className="mt-0.5 text-[10px] text-gridiron-cyan">AI vezényli · átveheted</div>
                      )}
                    </button>
                  ))}
                </div>

                {error && <p className="text-sm text-red-400">{error}</p>}

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setStep("league")}
                    className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300"
                  >
                    Vissza
                  </button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    type="button"
                    disabled={!selectedCode || submitting}
                    onClick={handleClaim}
                    className="flex-1 rounded-lg bg-gridiron-accent py-2 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-40"
                  >
                    {submitting
                      ? "Csapat lefoglalása..."
                      : `Csapat kiválasztása${selectedTeam ? `: ${selectedTeam.name}` : ""}`}
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </PageTransition>
  );
}
