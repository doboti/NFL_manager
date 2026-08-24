import { ReactNode } from "react";
import { motion } from "framer-motion";
import { Player } from "../api/client";
import { TIER_STYLES, getPlayerTier } from "../playerTier";
import PlayerAvatar from "./PlayerAvatar";

interface Props {
  player: Player;
  index?: number;
  footer?: ReactNode;
  subtitle?: ReactNode;
}

export default function PlayerCard({ player, index = 0, footer, subtitle }: Props) {
  const tier = getPlayerTier(player.overall);
  const style = TIER_STYLES[tier];

  return (
    <motion.div
      initial={{ opacity: 0, rotateY: -75, scale: 0.85 }}
      animate={{ opacity: 1, rotateY: 0, scale: 1 }}
      transition={{ duration: 0.45, delay: Math.min(index, 12) * 0.04, ease: "easeOut" }}
      whileHover={{ y: -4, scale: 1.02 }}
      className={`relative overflow-hidden rounded-xl border-2 p-3 shadow-lg ${style.card}`}
      style={{ transformStyle: "preserve-3d" }}
    >
      {style.shimmer && (
        <motion.div
          className="pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-white/50 blur-sm animate-shimmer"
          aria-hidden
        />
      )}

      <div className="relative flex items-start justify-between">
        <div className={`text-3xl font-black leading-none tracking-tight ${style.ovr}`}>{player.overall}</div>
        <span className="rounded bg-black/25 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
          {player.position}
        </span>
      </div>

      <div className="relative my-2 flex justify-center">
        <PlayerAvatar firstName={player.first_name} lastName={player.last_name} photoUrl={player.photo_url} size={72} />
      </div>

      <div className="relative text-center">
        <div className="truncate text-sm font-bold">
          {player.first_name} {player.last_name}
        </div>
        <div className={`text-xs ${style.meta}`}>
          {player.age} éves{player.nfl_team && ` · ${player.nfl_team}`}
        </div>
        {subtitle}
      </div>

      {footer && <div className="relative mt-2">{footer}</div>}
    </motion.div>
  );
}
