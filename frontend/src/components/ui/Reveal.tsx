"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  delay?: number;
  y?: number;
  duration?: number;
  className?: string;
  as?: keyof React.JSX.IntrinsicElements;
};

/**
 * Reveal — wraps content in a Framer Motion scroll-in animation.
 * Defaults to a soft 24px rise + fade.
 */
export function Reveal({ children, delay = 0, y = 24, duration = 0.7, className }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
      transition={{ duration, ease: [0.2, 0.8, 0.2, 1], delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}