import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Profile, changePassword, fetchProfile } from "../api/client";
import { useAuth } from "../context/AuthContext";
import PageTransition from "../components/PageTransition";
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

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProfile()
      .then(setProfile)
      .catch(() => setError("Nem sikerült betölteni a profilt."));
  }, []);

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-gridiron-accent">Profil</h1>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.96 }}
            onClick={logout}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-red-400 hover:text-red-400"
          >
            Kijelentkezés
          </motion.button>
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
              <div className="mb-1 text-lg font-semibold">{profile.display_name}</div>
              <div className="mb-3 text-sm text-slate-500">{profile.email}</div>
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <span>
                  Szint: <span className="font-bold text-gridiron-accent">{profile.level}</span>
                </span>
                <span className="text-slate-500">
                  Lezárt szezonok: {profile.completed_seasons}
                </span>
                <span className="text-slate-500">
                  Liga-slotok: {profile.unlocked_slots}/{profile.total_slots}
                </span>
              </div>
              {profile.next_slot && (
                <p className="mt-2 text-xs text-slate-500">
                  A(z) {profile.next_slot.slot}. slot {profile.next_slot.required_level}. szinten nyílik meg.
                </p>
              )}
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate("/select-team")}
              className="mb-6 w-full rounded-lg bg-gridiron-accent py-3 font-semibold text-slate-950 transition hover:brightness-110"
            >
              Liga és csapat választása
            </motion.button>

            <h2 className="mb-3 text-xl font-semibold">
              Trófeák{" "}
              <span className="text-sm font-normal text-slate-500">
                ({profile.achievements.filter((a) => a.earned).length}/{profile.achievements.length})
              </span>
            </h2>
            <div className="mb-8 grid gap-3 sm:grid-cols-2">
              {profile.achievements.map((a) => (
                <div
                  key={a.code}
                  className={`rounded-lg border p-3 text-sm ${
                    a.earned
                      ? "border-gridiron-accent/60 bg-gridiron-accent/10 text-gridiron-accent"
                      : "border-slate-800 bg-slate-900 text-slate-600"
                  }`}
                >
                  <div className="font-semibold">{a.name}</div>
                  <div className={a.earned ? "text-xs text-slate-300" : "text-xs text-slate-600"}>
                    {a.description}
                  </div>
                </div>
              ))}
            </div>

            <h2 className="mb-3 text-xl font-semibold">Jelszó módosítása</h2>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
              <PasswordChangeForm />
            </div>
          </>
        )}
      </div>
    </PageTransition>
  );
}
