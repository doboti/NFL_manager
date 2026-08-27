import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Building2,
  Dice5,
  Landmark,
  LucideIcon,
  Repeat,
  ShieldCheck,
  Store,
  Swords,
  TrendingUp,
  Zap,
} from "lucide-react";
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
import PlayerAvatar from "../../components/PlayerAvatar";
import { Card, PrimaryButton, SectionHeading } from "../../components/ui";
import { useVirtualTime } from "../../context/TimeContext";

interface Props {
  team: Team;
  onTeamUpdate: (team: Team) => void;
}

const SPONSOR_ICONS: Record<string, LucideIcon> = {
  steady: ShieldCheck,
  performance: TrendingUp,
  high_risk: Dice5,
  short_term: Zap,
  local_business: Store,
};

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

      <Card highlight className="mb-6">
        <h2 className="mb-3 flex items-center gap-2 font-semibold">
          <Swords size={16} className="text-team-text" /> Következő meccs
        </h2>
        {upcoming ? (
          <>
            <div className="flex items-center justify-between gap-2">
              <div className="flex flex-1 flex-col items-center gap-1.5">
                <PlayerAvatar firstName={team.name} lastName="" photoUrl={team.logo_url} size={48} />
                <span className="max-w-full truncate text-xs font-semibold text-slate-200">{team.name}</span>
              </div>
              <div className="flex shrink-0 flex-col items-center gap-1 px-1">
                <span className="text-lg font-black text-slate-600">VS</span>
                <span className="text-xs font-bold text-team-text">
                  <CountdownText target={upcoming.scheduled_at} />
                </span>
                <span className="rounded bg-black/30 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-400">
                  {upcoming.home_team_id === team.id ? "Hazai" : "Vendég"}
                </span>
              </div>
              <div className="flex flex-1 flex-col items-center gap-1.5">
                <PlayerAvatar
                  firstName={upcoming.home_team_id === team.id ? upcoming.away_team_name : upcoming.home_team_name}
                  lastName=""
                  photoUrl={upcoming.home_team_id === team.id ? upcoming.away_team_logo_url : upcoming.home_team_logo_url}
                  size={48}
                />
                <span className="max-w-full truncate text-xs font-semibold text-slate-200">
                  {upcoming.home_team_id === team.id ? upcoming.away_team_name : upcoming.home_team_name}
                </span>
              </div>
            </div>
            <p className="mt-3 text-center text-xs text-slate-500">
              {new Date(upcoming.scheduled_at).toLocaleString("hu-HU")}
            </p>
            <p className="mt-1 text-center text-xs font-semibold text-team-text">
              Esély a győzelemre:{" "}
              {Math.round(
                (upcoming.home_team_id === team.id
                  ? upcoming.home_win_probability
                  : 1 - upcoming.home_win_probability) * 100
              )}
              %
            </p>
          </>
        ) : (
          <p className="text-sm text-slate-400">
            Következő meccs: {new Date(team.next_match_at).toLocaleString("hu-HU")} · hátra:{" "}
            <CountdownText target={team.next_match_at} />
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
              <>
                <p className="mb-2 text-sm text-slate-400">
                  Fejlesztés {upgrade.target_level}. szintre · hátra: <CountdownText target={upgrade.ends_at} />
                </p>
                <div className="h-2 w-full overflow-hidden rounded-full bg-black/30">
                  <motion.div
                    className="h-2 rounded-full bg-team-primary"
                    initial={false}
                    animate={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          2,
                          ((virtualNow() - new Date(upgrade.started_at).getTime()) /
                            (new Date(upgrade.ends_at).getTime() - new Date(upgrade.started_at).getTime())) *
                            100
                        )
                      )}%`,
                    }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
                </div>
              </>
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
        {sponsors.map((s, i) => {
          const Icon = SPONSOR_ICONS[s.template_key] ?? Landmark;
          return (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="text-sm">
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2 font-semibold">
                    <Icon size={15} className="text-team-text" />
                    {s.name}
                  </div>
                  <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-emerald-400">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    </span>
                    Aktív
                  </span>
                </div>
                <div className="font-stat text-slate-400">
                  {s.daily_amount.toLocaleString("hu-HU")} FT/nap
                  {s.win_bonus > 0 && ` + ${s.win_bonus.toLocaleString("hu-HU")} FT győzelmi bónusz`}
                </div>
                <div className="mb-2 text-slate-500">
                  Lejár: <CountdownText target={s.expires_at} />
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-black/30">
                  <motion.div
                    className="h-1.5 rounded-full bg-team-primary"
                    initial={false}
                    animate={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          2,
                          ((virtualNow() - new Date(s.signed_at).getTime()) /
                            (new Date(s.expires_at).getTime() - new Date(s.signed_at).getTime())) *
                            100
                        )
                      )}%`,
                    }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
                </div>
              </Card>
            </motion.div>
          );
        })}
        {sponsors.length < 3 &&
          templates
            .filter((t) => !signedKeys.has(t.key))
            .map((t) => {
              const Icon = SPONSOR_ICONS[t.key] ?? Landmark;
              return (
              <Card key={t.key} dashed className="text-sm">
                <div className="mb-1 flex items-center gap-2 font-semibold">
                  <Icon size={15} className="text-slate-400" />
                  {t.name}
                </div>
                <div className="font-stat text-slate-400">
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
              );
            })}
      </div>

      <div className="rounded-lg border border-red-900/40 bg-red-950/10 p-4">
        <h2 className="mb-1 font-semibold text-red-400">Csapatváltás</h2>
        <p className="mb-3 text-xs text-slate-500">
          Feladod a(z) {team.name} irányítását -- egy AI veszi át azonnal. A felszabaduló liga-slotot a Profil
          oldalon tudod újra felhasználni.
        </p>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          disabled={busy === "release"}
          onClick={() =>
            withBusy("release", async () => {
              if (!confirm(`Biztosan feladod a(z) ${team.name} irányítását?`)) return;
              await releaseTeam(team.id);
              window.location.href = "/profile";
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
