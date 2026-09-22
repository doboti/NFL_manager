import { motion } from "framer-motion";
import { ReactNode } from "react";

export default function PageTransition({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0, pointerEvents: "auto" }}
      // pointerEvents isn't interpolated -- Framer Motion just applies it
      // once the exit animation starts, so a fading-out page can't eat
      // clicks meant for the page mounting in behind it. (usePresence()
      // would need an explicit safeToRemove() call, which AnimatePresence's
      // mode="wait" never gets without one -- that silently wedges EVERY
      // route transition in the app, so don't reach for it here.)
      exit={{ opacity: 0, y: -12, pointerEvents: "none" }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
