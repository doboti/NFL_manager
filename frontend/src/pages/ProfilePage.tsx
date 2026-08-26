import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Lock, Play, Settings, Trophy, X } from "lucide-react";
import { Profile, changePassword, fetchProfile } from "../api/client";
import { useAuth } from "../context/AuthContext";
import PageTransition from "../components/PageTransition";
import PlayerAvatar from "../components/PlayerAvatar";
import { SkeletonBlock } from "../components/Skeleton";

function PasswordChangeForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(false);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "A jelszó módosítása nem sikerült.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="mb-1 block text-xs text-slate-400">Jelenlegi jelszó</label>
        <input
          type="password"
          required
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-gridiron-accent"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs text-slate-400">Új jelszó (min. 8 karakter)</label>
        <input
          type="password"
          required
          minLength={8}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm outline-none focus:border-gridiron-accent"
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {success && <p className="text-xs text-gridiron-accent">Jelszó frissítve.</p>}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        type="submit"
        disabled={busy}
        className="rounded-lg bg-gridiron-accent px-4 py-1.5 text-sm font-semibold text-slate-950 disabled:opacity-40"
      >
        {busy ? "Mentés..." : "Jelszó módosítása"}
      </motion.button>
    </form>
  );
}

function LevelProgress({ profile }: { profile: Profile }) {
  if (!profile.next_slot) {
    return (
      <div className="mt-3">
        <div className="h-2 w-full overflow-hidden rounded-full bg-black/30">
          <div className="h-2 w-full rounded-full bg-gridiron-accent" />
        </div>
        <p className="mt-1 text-xs text-gridiron-accent">Minden liga-slot feloldva!</p>
      </div>
    );
  }

  const pct = Math.min(100, Math.max(4, (profile.level / profile.next_slot.required_level) * 100));

  return (
    <div className="mt-3">
      <div className="h-2 w-full overflow-hidden rounded-full bg-black/30">
        <motion.div
          className="h-2 rounded-full bg-gridiron-accent"
          initial={false}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <p className="mt-1 text-xs text-slate-500">
        {profile.next_slot.slot}. liga-slot a(z) {profile.next_slot.required_level}. szinten nyílik meg (jelenleg{" "}
        {profile.level}. szint).
      </p>
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [hoveredCode, setHoveredCode] = useState<string | null>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile()
      .then(setProfile)
      .catch(() => setError("Nem sikerült betölteni a profilt."));
  }, []);

  const earnedCount = profile?.achievements.filter((a) => a.earned).length ?? 0;

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-gridiron-accent">Profil</h1>
          <div className="flex gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSettingsOpen(true)}
              className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:border-gridiron-accent hover:text-gridiron-accent"
              aria-label="Beállítások"
            >
              <Settings size={18} />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              onClick={logout}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-red-400 hover:text-red-400"
            >
              Kijelentkezés
            </motion.button>
          </div>
        </div>

        {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

        {profile === null ? (
          <div className="space-y-4">
            <SkeletonBlock className="h-24 w-full" />
            <SkeletonBlock className="h-40 w-full" />
          </div>
        ) : (
          <>
            <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900 p-4">
              <div className="flex items-center gap-3">
                <PlayerAvatar
                  firstName={profile.display_name.split(" ")[0] ?? ""}
                  lastName={profile.display_name.split(" ").slice(1).join(" ")}
                  photoUrl={null}
                  size={52}
                />
                <div>
                  <div className="text-lg font-semibold">{profile.display_name}</div>
                  <div className="text-sm text-slate-500">{profile.email}</div>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
                <span>
                  Szint: <span className="font-bold text-gridiron-accent">{profile.level}</span>
                </span>
                <span className="text-slate-500">Lezárt szezonok: {profile.completed_seasons}</span>
                <span className="text-slate-500">
                  Liga-slotok: {profile.unlocked_slots}/{profile.total_slots}
                </span>
                <span className="text-slate-500">
                  Trófeák: {earnedCount}/{profile.achievements.length}
                </span>
              </div>

              <LevelProgress profile={profile} />
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              animate={{
                boxShadow: [
                  "0 0 0px rgba(52,211,153,0.35)",
                  "0 0 26px rgba(52,211,153,0.6)",
                  "0 0 0px rgba(52,211,153,0.35)",
                ],
              }}
              transition={{ boxShadow: { duration: 2.4, repeat: Infinity, ease: "easeInOut" } }}
              onClick={() => navigate("/select-team")}
              className="mb-6 flex w-full items-center justify-center gap-2 rounded-lg bg-gridiron-accent py-3 text-base font-bold text-slate-950 transition hover:brightness-110"
            >
              <Play size={20} fill="currentColor" />
              Liga és csapat választása
            </motion.button>

            <h2 className="mb-3 flex items-center gap-2 text-xl font-semibold">
              <Trophy size={18} className="text-gridiron-accent" />
              Trófeák{" "}
              <span className="text-sm font-normal text-slate-500">
                ({earnedCount}/{profile.achievements.length})
              </span>
            </h2>
            <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {profile.achievements.map((a) => (
                <div
                  key={a.code}
                  onMouseEnter={() => setHoveredCode(a.code)}
                  onMouseLeave={() => setHoveredCode((c) => (c === a.code ? null : c))}
                  className={`relative rounded-lg border p-3 text-sm transition ${
                    a.earned
                      ? "border-yellow-400/60 bg-gradient-to-br from-yellow-500/10 to-yellow-900/10 text-yellow-300 shadow-[0_0_12px_rgba(234,179,8,0.15)]"
                      : "border-slate-800 bg-slate-900 text-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 font-semibold">
                    {a.name}
                    {!a.earned && <Lock size={13} className="shrink-0 text-slate-600" />}
                  </div>
                  <div className={a.earned ? "text-xs text-slate-300" : "text-xs text-slate-600"}>
                    {a.description}
                  </div>

                  <AnimatePresence>
                    {!a.earned && a.progress_text && hoveredCode === a.code && (
                      <motion.div
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 4 }}
                        transition={{ duration: 0.15 }}
                        className="absolute inset-x-2 -top-8 z-10 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-300 shadow-lg"
                      >
                        {a.progress_text}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <AnimatePresence>
        {settingsOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
            onClick={() => setSettingsOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-sm rounded-xl border border-slate-800 bg-slate-900 p-4"
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Beállítások</h3>
                <button
                  onClick={() => setSettingsOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:text-slate-100"
                  aria-label="Bezárás"
                >
                  <X size={20} />
                </button>
              </div>
              <h4 className="mb-2 text-sm font-semibold text-slate-300">Jelszó módosítása</h4>
              <PasswordChangeForm />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  );
}
