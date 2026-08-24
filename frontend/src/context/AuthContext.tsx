import { createContext, useContext, useState, ReactNode } from "react";

interface AuthContextValue {
  token: string | null;
  setToken: (token: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(
    localStorage.getItem("access_token")
  );

  function setToken(next: string | null) {
    if (next) {
      localStorage.setItem("access_token", next);
    } else {
      localStorage.removeItem("access_token");
    }
    setTokenState(next);
  }

  function logout() {
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, setToken, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
