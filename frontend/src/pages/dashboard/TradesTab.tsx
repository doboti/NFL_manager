import { useEffect, useState } from "react";
import { ArrowLeftRight } from "lucide-react";
import {
  Player,
  Team,
  TeamSummary,
  TradeOffer,
  acceptTradeOffer,
  cancelTradeOffer,
  createTradeOffer,
  fetchMyTeam,
  fetchTeamRoster,
  listOtherTeams,
  listTradeOffers,
  rejectTradeOffer,
} from "../../api/client";
import PlayerAvatar from "../../components/PlayerAvatar";
import CountdownText from "../../components/CountdownText";
import { SkeletonBlock } from "../../components/Skeleton";
import { Card, PrimaryButton, SecondaryButton } from "../../components/ui";

interface Props {
  team: Team;
  onTeamUpdate: (team: Team) => void;
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Függőben",
  ACCEPTED: "Elfogadva",
  REJECTED: "Elutasítva",
  CANCELLED: "Visszavonva",
};

function OfferRow({
  offer,
  isIncoming,
  busy,
  onAccept,
  onReject,
  onCancel,
}: {
  offer: TradeOffer;
  isIncoming: boolean;
  busy: boolean;
  onAccept: () => void;
  onReject: () => void;
  onCancel: () => void;
}) {
  return (
    <Card className="text-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold">
          {isIncoming ? offer.from_team_name : offer.to_team_name}
        </span>
        <span className="text-xs text-slate-500">{STATUS_LABELS[offer.status]}</span>
      </div>
      <div className="flex flex-wrap items-center gap-2 text-slate-300">
        <PlayerAvatar
          firstName={offer.target_player.first_name}
          lastName={offer.target_player.last_name}
          photoUrl={offer.target_player.photo_url}
          size={32}
        />
        <span>
          {offer.target_player.first_name} {offer.target_player.last_name} ({offer.target_player.position})
        </span>
        <span className="text-slate-500">cserébe:</span>
        {offer.offered_player && (
          <>
            <PlayerAvatar
              firstName={offer.offered_player.first_name}
              lastName={offer.offered_player.last_name}
              photoUrl={offer.offered_player.photo_url}
              size={32}
            />
            <span>
              {offer.offered_player.first_name} {offer.offered_player.last_name}
            </span>
          </>
        )}
        {offer.cash_offer > 0 && <span>{offer.cash_offer.toLocaleString("hu-HU")} FT</span>}
        {!offer.offered_player && offer.cash_offer === 0 && <span className="text-slate-500">semmi</span>}
      </div>

      {offer.status === "PENDING" && offer.respond_at && (
        <p className="mt-1 text-xs text-slate-500">
          Válasz várható: <CountdownText target={offer.respond_at} />
        </p>
      )}

      {offer.status === "PENDING" && (
        <div className="mt-3 flex gap-2">
          {isIncoming ? (
            <>
              <PrimaryButton disabled={busy} onClick={onAccept} className="px-3 py-1 text-xs">
                Elfogadás
              </PrimaryButton>
              <SecondaryButton disabled={busy} onClick={onReject} className="px-3 py-1 text-xs">
                Elutasítás
              </SecondaryButton>
            </>
          ) : (
            <SecondaryButton disabled={busy} onClick={onCancel} className="px-3 py-1 text-xs">
              Visszavonás
            </SecondaryButton>
          )}
        </div>
      )}
    </Card>
  );
}

export default function TradesTab({ team, onTeamUpdate }: Props) {
  const [offers, setOffers] = useState<TradeOffer[] | null>(null);
  const [otherTeams, setOtherTeams] = useState<TeamSummary[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  const [targetRoster, setTargetRoster] = useState<Player[]>([]);
  const [targetPlayerId, setTargetPlayerId] = useState<number | null>(null);
  const [offeredPlayerId, setOfferedPlayerId] = useState<number | null>(null);
  const [cashOffer, setCashOffer] = useState("0");

  async function refresh() {
    const [offerData, teamsData] = await Promise.all([listTradeOffers(), listOtherTeams()]);
    setOffers(offerData);
    setOtherTeams(teamsData);
  }

  useEffect(() => {
    refresh().catch(() => setError("Nem sikerült betölteni a tárgyalásokat."));
  }, []);

  useEffect(() => {
    if (selectedTeamId === null) {
      setTargetRoster([]);
      return;
    }
    fetchTeamRoster(selectedTeamId)
      .then((r) => setTargetRoster(r.players))
      .catch(() => setError("Nem sikerült betölteni az ellenfél keretét."));
  }, [selectedTeamId]);

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

  function resetForm() {
    setShowForm(false);
    setSelectedTeamId(null);
    setTargetRoster([]);
    setTargetPlayerId(null);
    setOfferedPlayerId(null);
    setCashOffer("0");
  }

  const incoming = (offers ?? []).filter((o) => o.to_team_id === team.id);
  const outgoing = (offers ?? []).filter((o) => o.from_team_id === team.id);

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
      <p className="mb-4 text-xs text-slate-500">
        Az AI vezette csapatok a napi liga-ciklus során bírálják el a nekik küldött ajánlatokat (nagyjából valós
        áras ajánlatot fogadnak el).
      </p>

      <div className="mb-6">
        <PrimaryButton onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Mégse" : "Új ajánlat"}
        </PrimaryButton>

        {showForm && (
          <Card className="mt-4 space-y-3">
            <div>
              <label className="mb-1 block text-xs text-slate-400">Csapat</label>
              <select
                value={selectedTeamId ?? ""}
                onChange={(e) => {
                  setSelectedTeamId(e.target.value ? Number(e.target.value) : null);
                  setTargetPlayerId(null);
                }}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-team-primary"
              >
                <option value="">Válassz csapatot...</option>
                {otherTeams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                    {t.is_bot ? " (AI)" : ""}
                  </option>
                ))}
              </select>
            </div>

            {selectedTeamId !== null && (
              <div>
                <label className="mb-1 block text-xs text-slate-400">Kért játékos</label>
                <select
                  value={targetPlayerId ?? ""}
                  onChange={(e) => setTargetPlayerId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-team-primary"
                >
                  <option value="">Válassz játékost...</option>
                  {targetRoster.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.first_name} {p.last_name} ({p.position}, OVR {p.overall})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="mb-1 block text-xs text-slate-400">Felajánlott saját játékos (opcionális)</label>
              <select
                value={offeredPlayerId ?? ""}
                onChange={(e) => setOfferedPlayerId(e.target.value ? Number(e.target.value) : null)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-team-primary"
              >
                <option value="">Nincs</option>
                {team.players.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name} ({p.position}, OVR {p.overall})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs text-slate-400">Készpénz felajánlás (FT)</label>
              <input
                type="number"
                min={0}
                value={cashOffer}
                onChange={(e) => setCashOffer(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-team-primary"
              />
            </div>

            <PrimaryButton
              disabled={!selectedTeamId || !targetPlayerId || busy === "create-offer"}
              onClick={() =>
                withBusy("create-offer", async () => {
                  if (!selectedTeamId || !targetPlayerId) return;
                  await createTradeOffer(selectedTeamId, targetPlayerId, offeredPlayerId, Number(cashOffer) || 0);
                  resetForm();
                  await refresh();
                })
              }
              className="w-full"
            >
              Ajánlat küldése
            </PrimaryButton>
          </Card>
        )}
      </div>

      <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
        <ArrowLeftRight size={16} className="text-team-text" /> Bejövő ajánlatok
      </h2>
      <div className="mb-6 space-y-2">
        {offers === null && (
          <>
            <SkeletonBlock className="h-16 w-full" />
            <SkeletonBlock className="h-16 w-full" />
          </>
        )}
        {offers !== null && incoming.length === 0 && <p className="text-sm text-slate-500">Nincs bejövő ajánlat.</p>}
        {incoming.map((o) => (
          <OfferRow
            key={o.id}
            offer={o}
            isIncoming
            busy={busy === `offer-${o.id}`}
            onAccept={() =>
              withBusy(`offer-${o.id}`, async () => {
                await acceptTradeOffer(o.id);
                onTeamUpdate(await fetchMyTeam());
                await refresh();
              })
            }
            onReject={() =>
              withBusy(`offer-${o.id}`, async () => {
                await rejectTradeOffer(o.id);
                await refresh();
              })
            }
            onCancel={() => undefined}
          />
        ))}
      </div>

      <h2 className="mb-3 text-lg font-semibold">Küldött ajánlatok</h2>
      <div className="space-y-2">
        {offers !== null && outgoing.length === 0 && <p className="text-sm text-slate-500">Nincs küldött ajánlat.</p>}
        {outgoing.map((o) => (
          <OfferRow
            key={o.id}
            offer={o}
            isIncoming={false}
            busy={busy === `offer-${o.id}`}
            onAccept={() => undefined}
            onReject={() => undefined}
            onCancel={() =>
              withBusy(`offer-${o.id}`, async () => {
                await cancelTradeOffer(o.id);
                await refresh();
              })
            }
          />
        ))}
      </div>
    </div>
  );
}
