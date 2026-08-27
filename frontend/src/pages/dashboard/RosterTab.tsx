import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users } from "lucide-react";
import {
  Player,
  Team,
  TrainingSession,
  cancelTraining,
  collectTraining,
  fetchMyTeam,
  listPlayerForTransfer,
  listTraining,
  releasePlayer,
  setLineup,
  startTraining,
  unlistPlayerFromTransfer,
} from "../../api/client";
import PlayerCard from "../../components/PlayerCard";
import { SkeletonCardGrid } from "../../components/Skeleton";
import CountdownText from "../../components/CountdownText";
import { Card, PrimaryButton, SectionHeading } from "../../components/ui";
import { useVirtualTime } from "../../context/TimeContext";

interface Props {
  team: Team;
  onTeamUpdate: (team: Team) => void;
}

function slotLabel(position: string, index?: number): string {
  if (position === "RB") return `RB${index}`;
  if (position === "WR") return `WR${index}`;
  return position;
}

function LineupPicker({
  team,
  onTeamUpdate,
  trainingPlayerIds,
  injuredPlayerIds,
}: Props & { trainingPlayerIds: Set<number>; injuredPlayerIds: Set<number> }) {
  const [qbId, setQbId] = useState<number | null>(null);
  const [rbIds, setRbIds] = useState<(number | null)[]>([null, null]);
  const [wrIds, setWrIds] = useState<(number | null)[]>([null, null]);
  const [teId, setTeId] = useState<number | null>(null);
  const [defId, setDefId] = useState<number | null>(null);
  const [kId, setKId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const starters = team.players.filter(
      (p) => p.is_starter && !trainingPlayerIds.has(p.id) && !injuredPlayerIds.has(p.id)
    );
    setQbId(starters.find((p) => p.position === "QB")?.id ?? null);
    const rbs = starters.filter((p) => p.position === "RB");
    setRbIds([rbs[0]?.id ?? null, rbs[1]?.id ?? null]);
    const wrs = starters.filter((p) => p.position === "WR");
    setWrIds([wrs[0]?.id ?? null, wrs[1]?.id ?? null]);
    setTeId(starters.find((p) => p.position === "TE")?.id ?? null);
    setDefId(starters.find((p) => p.position === "DEF")?.id ?? null);
    setKId(starters.find((p) => p.position === "K")?.id ?? null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team.players]);

  const selectable = team.players.filter((p) => !trainingPlayerIds.has(p.id) && !injuredPlayerIds.has(p.id));
  const byPosition: Record<string, Player[]> = {
    QB: selectable.filter((p) => p.position === "QB"),
    RB: selectable.filter((p) => p.position === "RB"),
    WR: selectable.filter((p) => p.position === "WR"),
    TE: selectable.filter((p) => p.position === "TE"),
    DEF: selectable.filter((p) => p.position === "DEF"),
    K: selectable.filter((p) => p.position === "K"),
  };

  const slots: { position: string; index?: number; value: number | null; onChange: (v: number | null) => void }[] = [
    { position: "QB", value: qbId, onChange: setQbId },
    { position: "RB", index: 1, value: rbIds[0], onChange: (v) => setRbIds([v, rbIds[1]]) },
    { position: "RB", index: 2, value: rbIds[1], onChange: (v) => setRbIds([rbIds[0], v]) },
    { position: "WR", index: 1, value: wrIds[0], onChange: (v) => setWrIds([v, wrIds[1]]) },
    { position: "WR", index: 2, value: wrIds[1], onChange: (v) => setWrIds([wrIds[0], v]) },
    { position: "TE", value: teId, onChange: setTeId },
    { position: "DEF", value: defId, onChange: setDefId },
    { position: "K", value: kId, onChange: setKId },
  ];

  const allChosen = [qbId, ...rbIds, ...wrIds, teId, defId, kId];
  const nonNullChosen = allChosen.filter((v): v is number => v !== null);
  const hasDuplicates = new Set(nonNullChosen).size !== nonNullChosen.length;

  async function handleSave() {
    if (hasDuplicates) return;
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      await setLineup(qbId, rbIds, wrIds, teId, defId, kId);
      onTeamUpdate(await fetchMyTeam());
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setError("Nem sikerült menteni a felállást. Ellenőrizd, hogy nincs-e ismétlődő játékos.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="mb-8">
      <h2 className="mb-1 text-lg font-semibold">Kezdőcsapat</h2>
      <p className="mb-3 text-xs text-slate-500">
        Válaszd ki, ki induljon a következő meccsen. Amit nem állítasz be, azt a rendszer automatikusan a
        legjobb OVR-ű játékossal tölti fel. Az épp edzésben lévő vagy sérült játékosok nem választhatók,
        amíg fel nem épülnek.
      </p>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {slots.map((slot, i) => (
          <div key={i}>
            <label className="mb-0.5 block text-[10px] uppercase tracking-wide text-slate-500">
              {slotLabel(slot.position, slot.index)}
            </label>
            <select
              value={slot.value ?? ""}
              onChange={(e) => slot.onChange(e.target.value ? Number(e.target.value) : null)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-2 py-1.5 text-xs outline-none focus:border-team-primary"
            >
              <option value="">Automatikus (legjobb OVR)</option>
              {byPosition[slot.position].map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} (OVR {p.overall})
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {hasDuplicates && (
        <p className="mt-2 text-xs text-red-400">Egy játékos csak egy pozíción szerepelhet.</p>
      )}
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}

      <PrimaryButton disabled={hasDuplicates || busy} onClick={handleSave} className="mt-3">
        {saved ? "Mentve!" : busy ? "Mentés..." : "Felállás mentése"}
      </PrimaryButton>
    </Card>
  );
}

export default function RosterTab({ team, onTeamUpdate }: Props) {
  const [training, setTraining] = useState<TrainingSession[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [listingPlayerId, setListingPlayerId] = useState<number | null>(null);
  const [askingPrice, setAskingPrice] = useState("");
  const { virtualNow } = useVirtualTime();

  useEffect(() => {
    listTraining()
      .then(setTraining)
      .catch(() => setError("Nem sikerült betölteni az edzéseket."));
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

  if (training === null) {
    return (
      <div>
        <SectionHeading icon={Users}>Keret</SectionHeading>
        <SkeletonCardGrid count={8} />
      </div>
    );
  }

  const trainingByPlayer = new Map(training.map((t) => [t.player_id, t]));
  const trainingPlayerIds = new Set(
    training.filter((t) => !t.collected && new Date(t.ends_at).getTime() > virtualNow()).map((t) => t.player_id)
  );
  const injuredPlayerIds = new Set(
    team.players.filter((p) => p.injured_until && new Date(p.injured_until).getTime() > virtualNow()).map((p) => p.id)
  );

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <LineupPicker
        team={team}
        onTeamUpdate={onTeamUpdate}
        trainingPlayerIds={trainingPlayerIds}
        injuredPlayerIds={injuredPlayerIds}
      />

      <SectionHeading icon={Users}>Keret · Edzésslotok: {training.length}/3</SectionHeading>
      <p className="mb-3 -mt-2 text-xs text-slate-500">
        Az edzés minden játékos egyéni potenciáljáig fejleszti az OVR-t -- minél közelebb vagy hozzá, annál több
        edzés kell egy pontért.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" style={{ perspective: 1000 }}>
        {team.players.map((player, i) => {
          const session = trainingByPlayer.get(player.id);
          const ready = session && new Date(session.ends_at).getTime() <= virtualNow();
          const isInjured = injuredPlayerIds.has(player.id);
          const isListing = listingPlayerId === player.id;

          return (
            <PlayerCard
              key={player.id}
              player={player}
              index={i}
              subtitle={
                <div className="mt-2">
                  {player.is_starter && (
                    <div className="mb-1 inline-block rounded bg-black/30 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide">
                      Kezdő
                    </div>
                  )}
                  {isInjured && (
                    <div className="mb-1 ml-1 inline-flex items-center gap-1 rounded bg-red-950/60 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-red-300">
                      <span className="relative flex h-1.5 w-1.5">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-red-400" />
                      </span>
                      Sérült
                    </div>
                  )}
                  <div className="mt-0.5 text-[10px] opacity-70">
                    {player.potential !== null && player.overall >= player.potential ? (
                      <>Elérte a potenciálját ({player.potential})</>
                    ) : (
                      <>
                        Potenciál: {player.potential ?? 99} · {player.xp}/{player.sessions_to_next_point} edzés a
                        köv. pontig
                      </>
                    )}
                  </div>
                </div>
              }
              footer={
                <div className="space-y-1.5">
                  {isInjured && (
                    <p className="rounded-lg bg-red-950/40 py-1.5 text-center text-xs font-medium text-red-300">
                      Sérült · felépül: <CountdownText target={player.injured_until as string} />
                    </p>
                  )}
                  {!session && !isInjured && (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.96 }}
                      disabled={busy === `train-${player.id}` || training.length >= 3}
                      onClick={() =>
                        withBusy(`train-${player.id}`, async () => {
                          await startTraining(player.id);
                          setTraining(await listTraining());
                        })
                      }
                      className="w-full rounded-lg bg-slate-950/80 py-1.5 text-xs font-semibold text-white hover:bg-slate-950 disabled:opacity-40"
                    >
                      Edzés indítása
                    </motion.button>
                  )}
                  {session && !ready && (
                    <>
                      <p className="flex items-center justify-center gap-1.5 rounded-lg bg-black/20 py-1.5 text-center text-xs font-medium">
                        <span className="relative flex h-1.5 w-1.5">
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-team-primary opacity-75" />
                          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-team-primary" />
                        </span>
                        Edzésben · hátra: <CountdownText target={session.ends_at} />
                      </p>
                      <button
                        disabled={busy === `cancel-${player.id}`}
                        onClick={() =>
                          withBusy(`cancel-${player.id}`, async () => {
                            if (
                              !window.confirm(
                                `Biztosan leállítod ${player.first_name} ${player.last_name} edzését? Az eddigi fejlődése nem fog befejeződni, elvész.`
                              )
                            )
                              return;
                            await cancelTraining(session.id);
                            setTraining(await listTraining());
                          })
                        }
                        className="w-full rounded-lg bg-black/20 py-1 text-[11px] font-semibold hover:bg-red-950/60 hover:text-red-300 disabled:opacity-30"
                      >
                        Edzés leállítása
                      </button>
                    </>
                  )}
                  {session && ready && (
                    <PrimaryButton
                      animate={{ opacity: [0.6, 1] }}
                      transition={{ opacity: { duration: 1, repeat: Infinity, repeatType: "reverse" } }}
                      disabled={busy === `collect-${player.id}`}
                      onClick={() =>
                        withBusy(`collect-${player.id}`, async () => {
                          await collectTraining(session.id);
                          onTeamUpdate(await fetchMyTeam());
                          setTraining(await listTraining());
                        })
                      }
                      className="w-full py-1.5 text-xs"
                    >
                      XP begyűjtése
                    </PrimaryButton>
                  )}

                  <div className="flex gap-1.5">
                    <button
                      disabled={busy === `release-${player.id}`}
                      onClick={() =>
                        withBusy(`release-${player.id}`, async () => {
                          if (!window.confirm(`Biztosan elengeded ${player.first_name} ${player.last_name}-t?`)) return;
                          await releasePlayer(player.id);
                          onTeamUpdate(await fetchMyTeam());
                          setTraining(await listTraining());
                        })
                      }
                      className="flex-1 rounded-lg bg-black/20 py-1 text-[11px] font-semibold hover:bg-red-950/60 hover:text-red-300 disabled:opacity-30"
                    >
                      Elenged
                    </button>

                    {player.listed_for_transfer ? (
                      <button
                        disabled={busy === `unlist-${player.id}`}
                        onClick={() =>
                          withBusy(`unlist-${player.id}`, async () => {
                            await unlistPlayerFromTransfer(player.id);
                            onTeamUpdate(await fetchMyTeam());
                          })
                        }
                        className="flex-1 rounded-lg bg-black/30 py-1 text-[11px] font-semibold"
                      >
                        Levétel ({player.asking_price?.toLocaleString("hu-HU")})
                      </button>
                    ) : isListing ? (
                      <div className="flex flex-1 gap-1">
                        <input
                          type="number"
                          autoFocus
                          value={askingPrice}
                          onChange={(e) => setAskingPrice(e.target.value)}
                          placeholder="Ár"
                          className="w-0 flex-1 rounded-lg bg-black/30 px-1.5 py-1 text-[11px] text-white outline-none placeholder:text-white/50"
                        />
                        <button
                          disabled={busy === `list-${player.id}` || !askingPrice}
                          onClick={() =>
                            withBusy(`list-${player.id}`, async () => {
                              await listPlayerForTransfer(player.id, Number(askingPrice));
                              setListingPlayerId(null);
                              setAskingPrice("");
                              onTeamUpdate(await fetchMyTeam());
                            })
                          }
                          className="rounded-lg bg-black/40 px-2 text-[11px] font-semibold"
                        >
                          Listázás
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => {
                          setListingPlayerId(player.id);
                          setAskingPrice("");
                        }}
                        className="flex-1 rounded-lg bg-black/20 py-1 text-[11px] font-semibold"
                      >
                        Transzferlistára
                      </button>
                    )}
                  </div>
                </div>
              }
            />
          );
        })}
      </div>
    </div>
  );
}
