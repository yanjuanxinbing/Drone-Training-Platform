"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./TelemetryStrip.module.css";

const COUNTERS = [
  { label: "Hours of synthetic flight logged", value: 184_320, suffix: " h" },
  { label: "Pilots in active training", value: 1_274, suffix: "" },
  { label: "Mean scenario completion rate", value: 87, suffix: "%" },
  { label: "Mean objective precision", value: 0.34, suffix: " m", decimals: 2 },
  { label: "Real-time AirSim bridges online", value: 12, suffix: "" },
];

export function TelemetryStrip() {
  return (
    <section className={styles.section} aria-label="Operational telemetry">
      <div className={styles.container}>
        <div className={styles.eyebrowRow}>
          <span>03</span>
          <span>Operational Telemetry</span>
          <span>Quarterly snapshot</span>
          <span>Q3 · 2026</span>
        </div>

        <div className={styles.strip}>
          {COUNTERS.map((c, i) => (
            <CounterCell key={c.label} {...c} delay={i * 80} />
          ))}
        </div>
      </div>
    </section>
  );
}

function CounterCell({
  label,
  value,
  suffix,
  decimals = 0,
  delay,
}: {
  label: string;
  value: number;
  suffix: string;
  decimals?: number;
  delay: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting && !started) {
            setStarted(true);
            const startTime = performance.now();
            const tick = (now: number) => {
              const t = Math.min(1, (now - startTime) / 1500);
              const eased = 1 - Math.pow(1 - t, 3);
              setShown(value * eased);
              if (t < 1) requestAnimationFrame(tick);
            };
            requestAnimationFrame(tick);
          }
        });
      },
      { threshold: 0.4 },
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [value, started]);

  const formatted = decimals > 0 ? shown.toFixed(decimals) : Math.round(shown).toLocaleString();

  return (
    <div className={styles.cell} ref={ref} style={{ transitionDelay: `${delay}ms` }}>
      <div className={styles.value}>
        <span className={styles.numeral}>{formatted}</span>
        <span className={styles.suffix}>{suffix}</span>
      </div>
      <div className={styles.label}>{label}</div>
      <div className={styles.tickRow}>
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}