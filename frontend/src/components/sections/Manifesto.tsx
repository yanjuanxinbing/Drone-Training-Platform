"use client";

import { Reveal } from "@/components/ui/Reveal";
import styles from "./Manifesto.module.css";

export function Manifesto() {
  return (
    <section className={styles.section}>
      <div className={styles.container}>
        <div className={styles.eyebrowRow}>
          <span>02</span>
          <span>Manifesto</span>
          <span>Three propositions</span>
          <span>§</span>
        </div>

        <div className={styles.headline}>
          <Reveal>
            <p className={styles.kicker}>Why a training platform, and not a course catalogue.</p>
          </Reveal>
          <Reveal delay={0.1}>
            <h2 className={styles.title}>
              Flying is a craft. We treat it like one — built from primitives, measured against the grid.
            </h2>
          </Reveal>
        </div>

        <ol className={styles.list}>
          {PROPOSITIONS.map((p, i) => (
            <li key={p.id} className={styles.item}>
              <Reveal delay={0.05 * i} y={20}>
                <div className={styles.itemHead}>
                  <span className={styles.itemNum}>{p.id}</span>
                  <span className={styles.itemKicker}>{p.kicker}</span>
                </div>
                <p className={styles.itemText}>{p.text}</p>
                <div className={styles.itemMeta}>
                  <span>{p.metric}</span>
                  <span>{p.tag}</span>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

const PROPOSITIONS = [
  {
    id: "I",
    kicker: "Instrument first.",
    text: "Every scenario exposes the same telemetry — altitude, attitude, link quality, battery — over an identical HUD. A pilot's fluency transfers because the instrument never lies about what changes.",
    metric: "12 channels",
    tag: "Telemetry",
  },
  {
    id: "II",
    kicker: "Restraint as a feature.",
    text: "We use six colours, one typeface, and twelve columns. The page does not perform — it tells the truth about the platform and gets out of the way of the pilot.",
    metric: "6 tokens",
    tag: "Design",
  },
  {
    id: "III",
    kicker: "Open by construction.",
    text: "Airframes, scenarios, and progress records belong to the operator. The backend speaks plain JSON; the simulator can fall back to the browser or hook up to a real AirSim rig without code changes.",
    metric: "REST + WS",
    tag: "Surface",
  },
];