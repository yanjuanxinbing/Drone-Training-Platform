import Link from "next/link";
import styles from "./Footer.module.css";

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          <div className={styles.brandCol}>
            <h2 className={styles.bigMark}>DRONE/TRAINING</h2>
            <p className={styles.tagline}>
              A multi-scenario training platform for civil and commercial pilots.
              Engineered with the precision of a Swiss workshop.
            </p>
            <p className={styles.fineprint}>
              © 2026 Drone/Training Platform. Released under a permissive licence. Made with Helvetica, restraint, and a great deal of coffee.
            </p>
          </div>

          <div>
            <h3 className={styles.colTitle}>Training</h3>
            <ul className={styles.colList}>
              <li><Link href="/training">All Scenarios</Link></li>
              <li><Link href="/training/urban">Urban Skyline</Link></li>
              <li><Link href="/training/forest">Forest Corridor</Link></li>
              <li><Link href="/training/indoor">Indoor Precision</Link></li>
              <li><Link href="/training/mountain">Alpine Ascent</Link></li>
              <li><Link href="/training/coastal">Coastal Survey</Link></li>
              <li><Link href="/training/industrial">Industrial Grid</Link></li>
            </ul>
          </div>

          <div>
            <h3 className={styles.colTitle}>Simulator</h3>
            <ul className={styles.colList}>
              <li><Link href="/simulator/urban">Urban</Link></li>
              <li><Link href="/simulator/forest">Forest</Link></li>
              <li><Link href="/simulator/indoor">Indoor</Link></li>
              <li><Link href="/simulator/mountain">Mountain</Link></li>
              <li><Link href="/simulator/coastal">Coastal</Link></li>
              <li><Link href="/simulator/industrial">Industrial</Link></li>
            </ul>
          </div>

          <div>
            <h3 className={styles.colTitle}>Index</h3>
            <ul className={styles.colList}>
              <li><Link href="/">00 · Home</Link></li>
              <li><Link href="/training">01 · Scenarios</Link></li>
              <li><Link href="/account">02 · Account</Link></li>
              <li><Link href="/account/progress">03 · Progress</Link></li>
            </ul>
          </div>
        </div>

        <div className={styles.endline}>
          <span className="t-meta">Designed in the Swiss Grid · 12 col × 8 px</span>
          <span className="t-meta">Bauhaus · Helvetica · Restraint</span>
        </div>
      </div>
    </footer>
  );
}