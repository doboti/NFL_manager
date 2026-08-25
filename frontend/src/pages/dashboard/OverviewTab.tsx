import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Building2, Landmark, Repeat } from "lucide-react";
import {
  ScheduledMatch,
  Sponsor,
  SponsorTemplate,
  StadiumUpgrade,
  Tactic,
  Team,
  collectStadiumUpgrade,
  fetchMyTeam,
  getSponsorTemplates,
  getStadiumUpgrade,
  getUpcomingMatch,
  listSponsors,
  releaseTeam,
  setTeamTactic,
  signSponsor,
  startStadiumUpgrade,
} from "../../api/client";
import { STADIUM_LEVELS, TACTIC_LABELS } from "../../gameData";
import CountdownText from "../../components/CountdownText";
import { Card, PrimaryButton, SectionHeading } from "../../components/ui";
import { useVirtualTime } from "../../context/TimeContext";

interface Props {
  team: Team;
  onTeamUpdate: (team: Team) => void;
}

export default function OverviewTab({ team, onTeamUpdate }: Props) {
  const [upgrade, setUpgrade] = useState<StadiumUpgrade | null>(null);
  const [sponsors, setSponsors] = useState<Sponsor[]>([]);
  const { virtualNow } = useVirtualTime();
  const [templates, setTemplates] = useState<SponsorTemplate[]>([]);
  const [upcoming, setUpcoming] = useState<ScheduledMatch | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const [upgradeData, sponsorData, templateData, upcomingData] = await Promise.all([
      getStadiumUpgrade(),
      listSponsors(),
      getSponsorTemplates(),
      getUpcomingMatch(),
    ]);
    setUpgrade(upgradeData);
    setSponsors(sponsorData);
    setTemplates(templateData);
    setUpcoming(upcomingData);
  }

  useEffect(() => {
    refresh().catch(() => setError("Nem sikerült betölteni az áttekintést."));
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

  const nextStadium = STADIUM_LEVELS[team.stadium_level + 1];
  const upgradeReady = upgrade && new Date(upgrade.ends_at).getTime() <= virtualNow();
  const signedKeys = new Set(sponsors.map((s) => s.template_key));

  return (
    <div>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <Card className="mb-6">
        <h2 className="mb-1 font-semibold">Liga</h2>
        <p className="text-sm text-slate-400">
          Következő meccs: {new Date(upcoming ? upcoming.scheduled_at : team.next_match_at).toLocaleString("hu-HU")} ·
          hátra: <CountdownText target={upcoming ? upcoming.scheduled_at : team.next_match_at} />
        </p>
        {upcoming && (
          <p className="mt-1 text-sm text-slate-300">
            Ellenfél:{" "}
            <span className="font-semibold text-team-text">
              {upcoming.home_team_id === team.id ? upcoming.away_team_name : upcoming.home_team_name}
            </span>{" "}
            ({upcoming.home_team_id === team.id ? "hazai" : "vendég"})
          </p>
        )}
      </Card>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <h2 className="mb-2 flex items-center gap-2 font-semibold">
            <Building2 size={16} className="text-team-text" /> Stadion
          </h2>
          {upgrade && !upgrade.collected ? (
            upgradeReady ? (
              <PrimaryButton
                disabled={busy === "collect-upgrade"}
                onClick={() =>
                  withBusy("collect-upgrade", async () => {
                    await collectStadiumUpgrade();
                    setUpgrade(null);
                    onTeamUpdate(await fetchMyTeam());
                  })
                }
                className="w-full"
              >
                Fejlesztés átvétele (szint {upgrade.target_level})
              </PrimaryButton>
            ) : (
              <p className="text-sm text-slate-400">
                Fejlesztés {upgrade.target_level}. szintre · hátra: <CountdownText target={upgrade.ends_at} />
              </p>
            )
          ) : nextStadium ? (
            <>
              <p className="mb-2 text-sm text-slate-400">
                Következő szint: {nextStadium.capacity.toLocaleString("hu-HU")} néző,{" "}
                {nextStadium.baseRevenue.toLocaleString("hu-HU")} FT/nap alapbevétel ·{" "}
                {nextStadium.upgradeHours}h építés
              </p>
              <PrimaryButton
                disabled={busy === "start-upgrade" || team.franchise_capital < nextStadium.upgradeCost}
                onClick={() =>
                  withBusy("start-upgrade", async () => {
                    const u = await startStadiumUpgrade();
                    setUpgrade(u);
                    onTeamUpdate(await fetchMyTeam());
                  })
                }
              >
                Fejlesztés indítása ({nextStadium.upgradeCost.toLocaleString("hu-HU")} FT)
              </PrimaryButton>
            </>
          ) : (
            <p className="text-sm text-slate-400">Maximális szint elérve.</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-2 flex items-center gap-2 font-semibold">
            <Repeat size={16} className="text-team-text" /> Taktika
          </h2>
          <select
            value={team.tactic}
            disabled={busy === "tactic"}
            onChange={(e) =>
              withBusy("tactic", async () => onTeamUpdate(await setTeamTactic(e.target.value as Tactic)))
            }
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-team-primary"
          >
            {Object.entries(TACTIC_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </Card>
      </div>

      <SectionHeading icon={Landmark}>Szponzorok ({sponsors.length}/3)</SectionHeading>
      <div className="mb-8 grid gap-3 sm:grid-cols-2">
        {sponsors.map((s, i) => (
          <motion.div
            key={s.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="text-sm">
              <div className="font-semibold">{s.name}</div>
              <div className="text-slate-400">
                {s.daily_amount.toLocaleString("hu-HU")} FT/nap
                {s.win_bonus > 0 && ` + ${s.win_bonus.toLocaleString("hu-HU")} FT győzelmi bónusz`}
              </div>
              <div className="text-slate-500">
                Lejár: <CountdownText target={s.expires_at} />
              </div>
            </Card>
          </motion.div>
        ))}
        {sponsors.length < 3 &&
          templates
            .filter((t) => !signedKeys.has(t.key))
            .map((t) => (
              <Card key={t.key} dashed className="text-sm">
                <div className="font-semibold">{t.name}</div>
                <div className="text-slate-400">
                  {t.daily_amount.toLocaleString("hu-HU")} FT/nap
                  {t.win_bonus > 0 && ` + ${t.win_bonus.toLocaleString("hu-HU")} FT győzelmi bónusz`}
                </div>
                <div className="mb-2 text-slate-500">Szerződés: {t.duration_days} nap</div>
                <PrimaryButton
                  disabled={busy === "sponsor"}
                  onClick={() =>
                    withBusy("sponsor", async () => {
                      await signSponsor(t.key);
                      setSponsors(await listSponsors());
                    })
                  }
                  className="px-3 py-1 text-xs"
                >
                  Aláírás
                </PrimaryButton>
              </Card>
            ))}
      </div>

      <div className="rounded-lg border border-red-900/40 bg-red-950/10 p-4">
        <h2 className="mb-1 font-semibold text-red-400">Csapatváltás</h2>
        <p className="mb-3 text-xs text-slate-500">
          Feladod a(z) {team.name} irányítását -- egy AI veszi át azonnal --, és a Csapatválasztásnál egy másik,
          jelenleg szabad csapatot választhatsz. A jelenlegi csapatod eddigi eredményei megmaradnak a
          szezon-történetében.
        </p>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          disabled={busy === "release"}
          onClick={() =>
            withBusy("release", async () => {
              if (!confirm(`Biztosan feladod a(z) ${team.name} irányítását?`)) return;
              await releaseTeam();
              window.location.href = "/select-team";
            })
          }
          className="rounded-lg border border-red-800 px-4 py-2 text-sm text-red-400 hover:bg-red-950/40 disabled:opacity-40"
        >
          {busy === "release" ? "..." : "Csapat feladása"}
        </motion.button>
      </div>
    </div>
  );
}
