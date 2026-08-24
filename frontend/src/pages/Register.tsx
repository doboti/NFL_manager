import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/client";
import { useAuth } from "../context/AuthContext";
import PageTransition from "../components/PageTransition";

export default function Register() {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { setToken } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const token = await register(email, password, displayName);
      setToken(token);
      navigate("/select-team");
    } catch {
      setError("Nem sikerült létrehozni a fiókot. Lehet, hogy ez az e-mail már foglalt.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageTransition>
      <div className="flex min-h-screen items-center justify-center px-4">
        <motion.form
          initial={{ scale: 0.96, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          onSubmit={handleSubmit}
          className="w-full max-w-sm space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-8 shadow-xl"
        >
          <h1 className="text-2xl font-bold text-gridiron-accent">Új fiók</h1>
          <p className="text-sm text-slate-400">
            Hozd létre a menedzser-profilodat. A csapatot a következő lépésben választod.
          </p>

          <input
            type="text"
            placeholder="Menedzser neve"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            minLength={2}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 outline-none focus:border-gridiron-accent"
          />
          <input
            type="email"
            placeholder="E-mail"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 outline-none focus:border-gridiron-accent"
          />
          <input
            type="password"
            placeholder="Jelszó (min. 8 karakter)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 outline-none focus:border-gridiron-accent"
          />

          {error && <p className="text-sm text-red-400">{error}</p>}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-gridiron-accent py-2 font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-40"
          >
            {submitting ? "Létrehozás..." : "Fiók létrehozása"}
          </motion.button>

          <p className="text-center text-sm text-slate-400">
            Már van fiókod?{" "}
            <Link to="/login" className="text-gridiron-accent hover:underline">
              Bejelentkezés
            </Link>
          </p>
        </motion.form>
      </div>
    </PageTransition>
  );
}
