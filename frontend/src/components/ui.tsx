import { ButtonHTMLAttributes, ReactNode } from "react";
import { HTMLMotionProps, motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { useTeamTheme } from "../context/TeamThemeContext";

interface CardProps {
  children: ReactNode;
  className?: string;
  highlight?: boolean;
  dashed?: boolean;
}

export function Card({ children, className = "", highlight = false, dashed = false }: CardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className={`rounded-xl p-4 shadow-sm transition-colors ${
        dashed
          ? "border border-dashed border-slate-700 bg-slate-900/50"
          : highlight
          ? "border border-team-primary/50 bg-team-primary/10"
          : "border border-slate-800/80 bg-slate-900/70"
      } ${className}`}
    >
      {children}
    </motion.div>
  );
}

type PrimaryButtonProps = HTMLMotionProps<"button"> & { children: ReactNode };

export function PrimaryButton({ children, className = "", style, ...rest }: PrimaryButtonProps) {
  const { contrastOnPrimary } = useTeamTheme();
  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.96 }}
      style={{ color: contrastOnPrimary, ...style }}
      className={`rounded-lg bg-team-primary px-4 py-2 text-sm font-semibold shadow-sm transition hover:brightness-110 disabled:opacity-40 ${className}`}
      {...rest}
    >
      {children}
    </motion.button>
  );
}

export function SecondaryButton({
  children,
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }) {
  return (
    <button
      className={`rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 transition hover:border-team-primary/60 hover:text-team-text disabled:opacity-40 ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export function SectionHeading({
  icon: Icon,
  children,
  className = "",
  right,
}: {
  icon?: LucideIcon;
  children: ReactNode;
  className?: string;
  right?: ReactNode;
}) {
  return (
    <div className={`mb-3 flex items-center justify-between ${className}`}>
      <h2 className="flex items-center gap-2 text-xl font-semibold text-slate-100">
        {Icon && <Icon size={18} className="text-team-text" />}
        {children}
      </h2>
      {right}
    </div>
  );
}
