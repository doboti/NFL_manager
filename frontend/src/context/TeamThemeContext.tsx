import { ReactNode, createContext, useContext, useMemo } from "react";
import { contrastText } from "../teamTheme";

interface TeamThemeValue {
  primary: string;
  secondary: string;
  contrastOnPrimary: "#000000" | "#ffffff";
}

const DEFAULT_THEME: TeamThemeValue = {
  primary: "#34d399",
  secondary: "#22d3ee",
  contrastOnPrimary: "#000000",
};

const TeamThemeContext = createContext<TeamThemeValue>(DEFAULT_THEME);

export function TeamThemeProvider({
  primary,
  secondary,
  children,
}: {
  primary: string;
  secondary: string;
  children: ReactNode;
}) {
  const value = useMemo<TeamThemeValue>(
    () => ({ primary, secondary, contrastOnPrimary: contrastText(primary) }),
    [primary, secondary]
  );
  return <TeamThemeContext.Provider value={value}>{children}</TeamThemeContext.Provider>;
}

export function useTeamTheme() {
  return useContext(TeamThemeContext);
}
