import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  LeagueInstance,
  LeagueOption,
  NFLTeamOption,
  claimTeam,
  createLeagueInstance,
  listAvailableLeagues,
  listAvailableTeams,
  listLeagueInstances,
} from "../api/client";
import PageTransition from "../components/PageTransition";

type Step = "league" | "instance" | "team";

export default function SelectTeam() {
  const [step, setStep] = useState<Step>("league");
  const [leagues, setLeagues] = useState<LeagueOption[]>([]);
  const [leaguesError, setLeaguesError] = useState<string | null>(null);
  const [selectedSport, setSelectedSport] = useState<string | null>(null);

  const [instances, setInstances] = useState<LeagueInstance[]>([]);
  const [instancesError, setInstancesError] = useState<string | null>(null);
  const [selectedInstanceKey, setSelectedInstanceKey] = useState<string | null>(null);
  const [creatingInstance, setCreatingInstance] = useState(false);

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
        setSelectedSport((prev) => prev ?? data[0]?.key ?? null);
      })
      .catch(() => setLeaguesError("Nem sikerült betölteni a ligalistát."));
  }, []);

  async function loadInstances(sport: string) {
    setInstancesError(null);
    try {
      const data = await listLeagueInstances(sport);
      setInstances(data);
      const open = data.find((i) => !i.is_full);
      setSelectedInstanceKey(open?.key ?? data[0]?.key ?? null);
      // Common case: exactly one, still-open instance -- skip straight to the team step.
      if (data.length === 1 && !data[0].is_full) {
        setSelectedInstanceKey(data[0].key);
        setStep("team");
      } else {
        setStep("instance");
      }
    } catch {
      setInstancesError("Nem sikerült betölteni a liga-példányokat.");
      setStep("instance");
    }
  }

  useEffect(() => {
    if (step !== "team" || !selectedInstanceKey) return;
    setTeams([]);
    setSelectedCode(null);
    listAvailableTeams(selectedInstanceKey)
      .then(setTeams)
      .catch(() => setTeamsError("Nem sikerült betölteni a csapatlistát."));
  }, [step, selectedInstanceKey]);

  async function handleStartNewInstance() {
    if (!selectedSport) return;
    setCreatingInstance(true);
    setInstancesError(null);
    try {
      const created = await createLeagueInstance(selectedSport);
      setSelectedInstanceKey(created.key);
      setStep("team");
    } catch (err: any) {
      setInstancesError(err?.response?.data?.detail ?? "Nem sikerült új ligát indítani.");
    } finally {
      setCreatingInstance(false);
    }
  }

  async function handleClaim() {
    if (!selectedCode || !selectedInstanceKey) return;
    setError(null);
    setSubmitting(true);
    try {
      await claimTeam(selectedInstanceKey, selectedCode);
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Nem sikerült lefoglalni ezt a csapatot. Lehet, hogy időközben más választotta.");
      listAvailableTeams(selectedInstanceKey).then(setTeams).catch(() => undefined);
    } finally {
      setSubmitting(false);
    }
  }

  const selectedTeam = teams.find((t) => t.code === selectedCode);
  const allInstancesFull = instances.length > 0 && instances.every((i) => i.is_full);

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
            <span className={step === "instance" ? "text-gridiron-accent" : ""}>2. Liga-példány</span>
            <span>→</span>
            <span className={step === "team" ? "text-gridiron-accent" : ""}>3. Csapat</span>
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
                  value={selectedSport ?? ""}
                  onChange={(e) => setSelectedSport(e.target.value)}
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
                  disabled={!selectedSport}
                  onClick={() => selectedSport && loadInstances(selectedSport)}
                  className="w-full rounded-lg bg-gridiron-accent py-2 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-40"
                >
                  Tovább
                </motion.button>
              </motion.div>
            )}

            {step === "instance" && (
              <motion.div
                key="instance"
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                <label className="block text-sm text-slate-400">
                  Válassz liga-példányt ({leagues.find((l) => l.key === selectedSport)?.name})
                </label>

                {instancesError && <p className="text-sm text-red-400">{instancesError}</p>}

                <div className="space-y-2">
                  {instances.map((i) => (
                    <button
                      key={i.key}
                      type="button"
                      disabled={i.is_full}
                      onClick={() => setSelectedInstanceKey(i.key)}
                      className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm transition ${
                        i.is_full
                          ? "cursor-not-allowed border-slate-800 bg-slate-900 text-slate-600"
                          : selectedInstanceKey === i.key
                          ? "border-gridiron-accent bg-gridiron-accent/10 text-gridiron-accent"
                          : "border-slate-700 bg-slate-800 text-slate-300 hover:border-gridiron-accent"
                      }`}
                    >
                      <span>{i.name}</span>
                      {i.is_full && <span className="text-xs">Tele</span>}
                    </button>
                  ))}
                </div>

                {allInstancesFull && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    type="button"
                    disabled={creatingInstance}
                    onClick={handleStartNewInstance}
                    className="w-full rounded-lg border border-dashed border-gridiron-accent/60 py-2 text-sm font-semibold text-gridiron-accent transition hover:bg-gridiron-accent/10 disabled:opacity-40"
                  >
                    {creatingInstance
                      ? "Liga indítása..."
                      : `Új ${leagues.find((l) => l.key === selectedSport)?.name} liga indítása`}
                  </motion.button>
                )}

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
                    disabled={!selectedInstanceKey || instances.find((i) => i.key === selectedInstanceKey)?.is_full}
                    onClick={() => setStep("team")}
                    className="flex-1 rounded-lg bg-gridiron-accent py-2 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-40"
                  >
                    Tovább
                  </motion.button>
                </div>
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
                  Válassz csapatot ({instances.find((i) => i.key === selectedInstanceKey)?.name ?? selectedInstanceKey})
                </label>

                {teamsError && <p className="text-sm text-red-400">{teamsError}</p>}

                <div className="grid max-h-80 grid-cols-3 gap-2 overflow-y-auto pr-1 sm:grid-cols-4">
                  {teams.map((t) => (
                    <button
                      key={t.code}
                      type="button"
                      disabled={t.taken}
                      onClick={() => setSelectedCode(t.code)}
                      className={`flex flex-col items-center gap-1 rounded-lg border px-2 py-3 text-center text-xs transition ${
                        t.taken
                          ? "cursor-not-allowed border-slate-800 bg-slate-900 text-slate-600"
                          : selectedCode === t.code
                          ? "border-gridiron-accent bg-gridiron-accent/10 text-gridiron-accent"
                          : "border-slate-700 bg-slate-800 text-slate-300 hover:border-gridiron-accent"
                      }`}
                    >
                      {t.logo_url ? (
                        <img
                          src={t.logo_url}
                          alt={t.name}
                          className={`h-12 w-12 object-contain ${t.taken ? "opacity-30 grayscale" : ""}`}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="h-12 w-12" />
                      )}
                      <div className="truncate font-semibold leading-tight">{t.taken ? "Foglalt" : t.name}</div>
                      {!t.taken && t.controlled_by_bot && (
                        <div className="text-[10px] text-gridiron-cyan">AI vezényli · átveheted</div>
                      )}
                    </button>
                  ))}
                </div>

                {error && <p className="text-sm text-red-400">{error}</p>}

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setStep("instance")}
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
