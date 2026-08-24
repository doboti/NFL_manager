import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/client";
import { useAuth } from "../context/AuthContext";
import PageTransition from "../components/PageTransition";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { setToken } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const token = await login(email, password);
      setToken(token);
      navigate("/");
    } catch {
      setError("Hibás e-mail vagy jelszó.");
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
        <h1 className="text-2xl font-bold text-gridiron-accent">Gridiron Manager</h1>
        <p className="text-sm text-slate-400">Jelentkezz be a franchise-odba.</p>

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
          placeholder="Jelszó"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 outline-none focus:border-gridiron-accent"
        />

        {error && <p className="text-sm text-red-400">{error}</p>}

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          type="submit"
          className="w-full rounded-lg bg-gridiron-accent py-2 font-semibold text-slate-950 transition hover:brightness-110"
        >
          Bejelentkezés
        </motion.button>

        <p className="text-center text-sm text-slate-400">
          Nincs még franchise-od?{" "}
          <Link to="/register" className="text-gridiron-accent hover:underline">
            Regisztráció
          </Link>
        </p>
      </motion.form>
    </div>
    </PageTransition>
  );
}
