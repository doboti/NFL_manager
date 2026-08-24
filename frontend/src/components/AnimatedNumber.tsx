import { useEffect, useRef } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";

interface AnimatedNumberProps {
  value: number;
  suffix?: string;
  locale?: string;
}

export default function AnimatedNumber({ value, suffix = "", locale = "hu-HU" }: AnimatedNumberProps) {
  const motionValue = useMotionValue(value);
  const rounded = useTransform(motionValue, (v) => Math.round(v).toLocaleString(locale));
  const previous = useRef(value);

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration: 0.8,
      ease: "easeOut",
    });
    previous.current = value;
    return controls.stop;
  }, [value, motionValue]);

  return (
    <>
      <motion.span>{rounded}</motion.span>
      {suffix}
    </>
  );
}
