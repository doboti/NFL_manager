import { useEffect, useState } from "react";
import { useVirtualTime } from "../context/TimeContext";

function formatRemaining(diffMs: number): string {
  if (diffMs <= 0) return "Kész";
  const totalMinutes = Math.floor(diffMs / 60_000);
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;

  if (days > 0) return `${days}n ${hours}ó`;
  return `${hours}ó ${minutes}p`;
}

export default function CountdownText({ target }: { target: string }) {
  const [, forceTick] = useState(0);
  const { virtualNow } = useVirtualTime();

  useEffect(() => {
    const interval = setInterval(() => forceTick((n) => n + 1), 30_000);
    return () => clearInterval(interval);
  }, []);

  const diffMs = new Date(target).getTime() - virtualNow();
  return <>{formatRemaining(diffMs)}</>;
}
