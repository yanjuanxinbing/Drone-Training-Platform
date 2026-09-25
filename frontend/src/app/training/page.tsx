import Link from "next/link";
import { SCENARIOS } from "@/lib/scenarios";
import { Reveal } from "@/components/ui/Reveal";
import styles from "./page.module.css";

export const metadata = {
  title: "Training · Drone/Training Platform",
};

export default function TrainingIndex() {
  return (
    <>
      <section className={styles.hero}>
        <div className={styles.container}>
          <div className={styles.eyebrowRow}>
            <span>00</span>
            <span>Training Console</span>
            <span>Six scenarios · three difficulties</span>
            <span>2026 · Q3</span>
          </div>

          <div className={styles.headline}>
            <Reveal>
              <h1 className={styles.title}>
                Choose a scenario.
                <br />
                <em>Six rooms, one instrument.</em>
              </h1>
            </Reveal>
            <Reveal delay={0.1}>
              <p className={styles.lede}>
                The training console is the entry point to every mission. Each
                card routes to a scenario detail page with objectives, success
                criteria, and an immediate route into the browser-based 3D
                simulator (or a live AirSim bridge if your rig is online).
              </p>
            </Reveal>
          </div>

          <div className={styles.filtersRow}>
            <span className={styles.filterChip} data-active="true">All</span>
            <span className={styles.filterChip}>Beginner</span>
            <span className={styles.filterChip}>Intermediate</span>
            <span className={styles.filterChip}>Advanced</span>
            <span className={styles.filterChip}>Expert</span>
          </div>
        </div>
      </section>

      <section className={styles.list}>
        <div className={styles.container}>
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
                    <span className={styles.cardNumber}>{s.number}</span>
                    <div className={styles.cardBody}>
                      <div className={styles.cardHead}>
                        <h3 className={styles.cardName}>{s.name}</h3>
                        <span className={styles.cardDifficulty}>{s.difficulty}</span>
                      </div>
                      <p className={styles.cardTagline}>{s.tagline}</p>
                      <ol className={styles.objectives}>
                        {s.objectives.slice(0, 3).map((o, idx) => (
                          <li key={idx}>
                            <span className={styles.objIndex}>
                              {String(idx + 1).padStart(2, "0")}
                            </span>
                            <span>{o}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                    <div className={styles.cardFoot}>
                      <span className={styles.duration}>
                        {s.duration_minutes} min
                      </span>
                      <span className={styles.cta}>
                        Open scenario <span aria-hidden="true">→</span>
                      </span>
                    </div>
                  </Link>
                </Reveal>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}