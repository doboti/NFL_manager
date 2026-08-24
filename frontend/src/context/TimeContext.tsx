import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { getTimeStatus } from "../api/client";
import { useAuth } from "./AuthContext";

interface TimeContextValue {
  offsetSeconds: number;
  setOffsetSeconds: (seconds: number) => void;
  virtualNow: () => number;
  refreshOffset: () => Promise<void>;
}

const TimeContext = createContext<TimeContextValue | undefined>(undefined);

export function TimeProvider({ children }: { children: ReactNode }) {
  const [offsetSeconds, setOffsetSeconds] = useState(0);
  const { token } = useAuth();

  async function refreshOffset() {
    if (!token) return;
    try {
      const status = await getTimeStatus();
      setOffsetSeconds(status.offset_seconds);
    } catch {
      // dev-only feature; a failed fetch just means "no offset applied"
    }
  }

  useEffect(() => {
    refreshOffset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function virtualNow(): number {
    return Date.now() + offsetSeconds * 1000;
  }

  return (
    <TimeContext.Provider value={{ offsetSeconds, setOffsetSeconds, virtualNow, refreshOffset }}>
      {children}
    </TimeContext.Provider>
  );
}

export function useVirtualTime() {
  const ctx = useContext(TimeContext);
  if (!ctx) throw new Error("useVirtualTime must be used within TimeProvider");
  return ctx;
}
