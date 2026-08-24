import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminUser, deleteAdminUser, listAdminUsers } from "../api/client";
import { useAuth } from "../context/AuthContext";
import PageTransition from "../components/PageTransition";
import { SkeletonBlock } from "../components/Skeleton";
import AdminTab from "./dashboard/AdminTab";

function UserManagementPanel() {
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    listAdminUsers()
      .then(setUsers)
      .catch(() => setError("Nem sikerült betölteni a felhasználókat."));
  }

  useEffect(load, []);

  async function handleDelete(user: AdminUser) {
    if (!confirm(`Biztosan törlöd ezt a fiókot: ${user.email}?`)) return;
    setBusyId(user.id);
    setError(null);
    try {
      await deleteAdminUser(user.id);
      setUsers((prev) => prev?.filter((u) => u.id !== user.id) ?? null);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "A törlés nem sikerült.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h2 className="mb-1 text-xl font-semibold">Felhasználók</h2>
      <p className="mb-4 text-xs text-slate-500">
        Csak olyan fiók törölhető, aminek a csapata még nem játszott meccset / nincs története.
      </p>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      {users === null ? (
        <SkeletonBlock className="h-40 w-full" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[10px] uppercase text-slate-600">
                <th className="p-3 font-medium">Email</th>
                <th className="p-3 font-medium">Név</th>
                <th className="p-3 font-medium">Csapat</th>
                <th className="p-3 font-medium">Típus</th>
                <th className="p-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-800 text-slate-300">
                  <td className="p-3">{u.email}</td>
                  <td className="p-3">{u.display_name}</td>
                  <td className="p-3">{u.team_name ?? "–"}</td>
                  <td className="p-3 text-xs">
                    {u.is_admin && <span className="mr-1 text-gridiron-accent">admin</span>}
                    {u.is_bot && <span className="text-gridiron-cyan">bot</span>}
                    {!u.is_admin && !u.is_bot && <span className="text-slate-500">játékos</span>}
                  </td>
                  <td className="p-3 text-right">
                    {!u.is_admin && (
                      <button
                        disabled={busyId === u.id}
                        onClick={() => handleDelete(u)}
                        className="rounded-lg border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-red-400 hover:text-red-400 disabled:opacity-40"
                      >
                        {busyId === u.id ? "..." : "Törlés"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function AdminPage() {
  const { logout } = useAuth();

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-gridiron-accent">Admin felület</h1>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.96 }}
            onClick={logout}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-red-400 hover:text-red-400"
          >
            Kijelentkezés
          </motion.button>
        </div>

        <div className="mb-10">
          <AdminTab />
        </div>

        <UserManagementPanel />
      </div>
    </PageTransition>
  );
}
