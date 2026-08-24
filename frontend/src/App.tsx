import { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { fetchMyTeam } from "./api/client";
import { SkeletonDashboard } from "./components/Skeleton";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SelectTeam from "./pages/SelectTeam";
import Dashboard from "./pages/Dashboard";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

type TeamStatus = "loading" | "has-team" | "no-team";

function useTeamStatus(): TeamStatus {
  const [status, setStatus] = useState<TeamStatus>("loading");
  const { token } = useAuth();

  useEffect(() => {
    if (!token) return;
    setStatus("loading");
    fetchMyTeam()
      .then(() => setStatus("has-team"))
      .catch(() => setStatus("no-team"));
  }, [token]);

  return status;
}

function RequireTeam({ children }: { children: JSX.Element }) {
  const status = useTeamStatus();
  if (status === "loading") return <SkeletonDashboard />;
  if (status === "no-team") return <Navigate to="/select-team" replace />;
  return children;
}

function RequireNoTeam({ children }: { children: JSX.Element }) {
  const status = useTeamStatus();
  if (status === "loading") return <SkeletonDashboard />;
  if (status === "has-team") return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/select-team"
          element={
            <RequireAuth>
              <RequireNoTeam>
                <SelectTeam />
              </RequireNoTeam>
            </RequireAuth>
          }
        />
        <Route
          path="/"
          element={
            <RequireAuth>
              <RequireTeam>
                <Dashboard />
              </RequireTeam>
            </RequireAuth>
          }
        />
      </Routes>
    </AnimatePresence>
  );
}
