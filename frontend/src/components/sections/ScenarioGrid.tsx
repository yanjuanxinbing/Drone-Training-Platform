"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { SCENARIOS } from "@/lib/scenarios";
import { Reveal } from "@/components/ui/Reveal";
import styles from "./ScenarioGrid.module.css";

export function ScenarioGrid() {
  return (
    <section className={styles.section} id="scenarios">
      <div className={styles.container}>
        <div className={styles.eyebrowRow}>
          <span>01</span>
          <span>Training Scenarios</span>
          <span>Six canonical environments</span>
          <span>00 — 06</span>
        </div>

        <div className={styles.intro}>
          <Reveal>
            <h2 className={styles.title}>
              Six canonical <em>training</em> grounds,
              <br />
              mapped onto a single instrument.
            </h2>
          </Reveal>
          <Reveal delay={0.1}>
            <p className={styles.lede}>
              Every pilot meets the same six problems in different disguises —
              urban interference, canopy cover, GPS denial, altitude drift,
              maritime corridors, and energized infrastructure. This is the
              training bench where each is rehearsed, instrumented, and graded.
            </p>
          </Reveal>
        </div>

        <ul className={styles.grid}>
          {SCENARIOS.map((s, i) => (
            <li key={s.slug} className={styles.cell}>
              <Reveal delay={i * 0.06} y={20}>
                <Link
                  href={`/training/${s.slug}`}
                  className={styles.card}
                  style={
                    {
                      "--card-color": s.color,
                      "--card-accent": s.accent,
                    } as React.CSSProperties
                  }
                >
                  <header className={styles.cardHeader}>
                    <span className={styles.cardNumber}>{s.number}</span>
                    <span className={styles.cardDifficulty}>{s.difficulty}</span>
                  </header>

                  <div className={styles.cardBody}>
                    <h3 className={styles.cardName}>{s.name}</h3>
                    <p className={styles.cardNameZh}>{s.name_zh}</p>
                    <p className={styles.cardTagline}>{s.tagline}</p>
                  </div>

                  <footer className={styles.cardFooter}>
                    <span className={styles.cardDuration}>
                      <span className={styles.cardDurationDot} aria-hidden="true" />
                      {s.duration_minutes} min · {s.objectives.length} objectives
                    </span>
                    <span className={styles.cardArrow} aria-hidden="true">
                      →
                    </span>
                  </footer>

                  <span className={styles.cardMark} aria-hidden="true" />
                </Link>
              </Reveal>
            </li>
          ))}
        </ul>

        <div className={styles.afterRow}>
          <Reveal delay={0.2}>
            <Link href="/training" className={styles.allLink}>
              <span className={styles.allLinkNum}>↗</span>
              <span>Open the full training console</span>
            </Link>
          </Reveal>
        </div>
      </div>
    </section>
  );
}