import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeftRight,
  CalendarDays,
  LayoutDashboard,
  LogOut,
  LucideIcon,
  Menu,
  ShoppingCart,
  Trophy,
  User,
  Users,
  X,
} from "lucide-react";
import { Team } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useTeamTheme } from "../context/TeamThemeContext";
import PlayerAvatar from "./PlayerAvatar";

export type TabKey = "overview" | "roster" | "market" | "trades" | "matches" | "league";

const NAV_ITEMS: { key: TabKey; label: string; icon: LucideIcon }[] = [
  { key: "overview", label: "Áttekintés", icon: LayoutDashboard },
  { key: "league", label: "Liga", icon: Trophy },
  { key: "roster", label: "Keret", icon: Users },
  { key: "market", label: "Piac", icon: ShoppingCart },
  { key: "trades", label: "Tárgyalások", icon: ArrowLeftRight },
  { key: "matches", label: "Meccsek", icon: CalendarDays },
];

interface Props {
  team: Team;
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

function NavList({ activeTab, onSelect }: { activeTab: TabKey; onSelect: (tab: TabKey) => void }) {
  const { contrastOnPrimary } = useTeamTheme();
  return (
    <nav className="flex flex-1 flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const active = item.key === activeTab;
        return (
          <button
            key={item.key}
            onClick={() => onSelect(item.key)}
            style={active ? { color: contrastOnPrimary } : undefined}
            className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              active ? "" : "text-slate-400 hover:text-slate-100"
            }`}
          >
            {active && (
              <motion.div
                layoutId="sidebar-active-pill"
                className="absolute inset-0 rounded-lg bg-team-primary"
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}
            <item.icon size={18} className="relative z-10" />
            <span className="relative z-10">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

function SidebarHeader({ team }: { team: Team }) {
  return (
    <div className="mb-6 flex items-center gap-3">
      <PlayerAvatar firstName={team.name} lastName="" photoUrl={team.logo_url} size={40} />
      <div className="min-w-0">
        <div className="truncate text-sm font-bold text-slate-100">{team.name}</div>
        <div className="text-xs text-slate-500">{team.wins}Gy {team.losses}V {team.ties}D</div>
      </div>
    </div>
  );
}

function SidebarFooter() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="mt-4 flex flex-col gap-1 border-t border-slate-800 pt-4">
      <button
        onClick={() => navigate("/profile")}
        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 transition-colors hover:text-slate-100"
      >
        <User size={18} />
        Profil
      </button>
      <button
        onClick={logout}
        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 transition-colors hover:text-red-400"
      >
        <LogOut size={18} />
        Kijelentkezés
      </button>
    </div>
  );
}

export default function Sidebar({ team, activeTab, onTabChange }: Props) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-4 z-30 rounded-lg border border-slate-800 bg-slate-900/90 p-2 text-slate-300 backdrop-blur lg:hidden"
        aria-label="Menü megnyitása"
      >
        <Menu size={20} />
      </button>

      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-800/80 bg-slate-950/60 p-4 lg:flex">
        <SidebarHeader team={team} />
        <NavList activeTab={activeTab} onSelect={onTabChange} />
        <SidebarFooter />
      </aside>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 z-40 bg-black/60 lg:hidden"
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
              className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-800 bg-slate-950 p-4 lg:hidden"
            >
              <div className="mb-2 flex justify-end">
                <button
                  onClick={() => setMobileOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:text-slate-100"
                  aria-label="Menü bezárása"
                >
                  <X size={20} />
                </button>
              </div>
              <SidebarHeader team={team} />
              <NavList
                activeTab={activeTab}
                onSelect={(tab) => {
                  onTabChange(tab);
                  setMobileOpen(false);
                }}
              />
              <SidebarFooter />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
