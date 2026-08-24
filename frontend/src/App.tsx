import { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { fetchCurrentUser, fetchMyTeam } from "./api/client";
import { SkeletonDashboard } from "./components/Skeleton";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SelectTeam from "./pages/SelectTeam";
import Dashboard from "./pages/Dashboard";
import AdminPage from "./pages/AdminPage";

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

type AdminStatus = "loading" | "admin" | "not-admin";

function useAdminStatus(): AdminStatus {
  const [status, setStatus] = useState<AdminStatus>("loading");
  const { token } = useAuth();

  useEffect(() => {
    if (!token) return;
    setStatus("loading");
    fetchCurrentUser()
      .then((user) => setStatus(user.is_admin ? "admin" : "not-admin"))
      .catch(() => setStatus("not-admin"));
  }, [token]);

  return status;
}

// Admin accounts skip league/team selection entirely -- they only get the
// admin console, never the regular player dashboard.
function RedirectAdminAway({ children }: { children: JSX.Element }) {
  const status = useAdminStatus();
  if (status === "loading") return <SkeletonDashboard />;
  if (status === "admin") return <Navigate to="/admin" replace />;
  return children;
}

function RequireAdmin({ children }: { children: JSX.Element }) {
  const status = useAdminStatus();
  if (status === "loading") return <SkeletonDashboard />;
  if (status === "not-admin") return <Navigate to="/" replace />;
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
          path="/admin"
          element={
            <RequireAuth>
              <RequireAdmin>
                <AdminPage />
              </RequireAdmin>
            </RequireAuth>
          }
        />
        <Route
          path="/select-team"
          element={
            <RequireAuth>
              <RedirectAdminAway>
                <RequireNoTeam>
                  <SelectTeam />
                </RequireNoTeam>
              </RedirectAdminAway>
            </RequireAuth>
          }
        />
        <Route
          path="/"
          element={
            <RequireAuth>
              <RedirectAdminAway>
                <RequireTeam>
                  <Dashboard />
                </RequireTeam>
              </RedirectAdminAway>
            </RequireAuth>
          }
        />
      </Routes>
    </AnimatePresence>
  );
}
