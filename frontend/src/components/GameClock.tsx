import { useEffect, useState } from "react";
import { useVirtualTime } from "../context/TimeContext";

export default function GameClock() {
  const [, forceTick] = useState(0);
  const { virtualNow } = useVirtualTime();

  useEffect(() => {
    const interval = setInterval(() => forceTick((n) => n + 1), 30_000);
    return () => clearInterval(interval);
  }, []);

  return <>{new Date(virtualNow()).toLocaleString("hu-HU")}</>;
}
