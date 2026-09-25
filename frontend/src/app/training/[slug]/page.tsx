import Link from "next/link";
import { notFound } from "next/navigation";
import { SCENARIOS, getScenario } from "@/lib/scenarios";
import { Reveal } from "@/components/ui/Reveal";
import styles from "./page.module.css";

type Params = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return SCENARIOS.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({ params }: Params) {
  const { slug } = await params;
  const s = getScenario(slug);
  if (!s) return {};
  return { title: `${s.name} · Training · Drone/Training Platform` };
}

export default async function ScenarioPage({ params }: Params) {
  const { slug } = await params;
  const scenario = getScenario(slug);
  if (!scenario) notFound();

  return (
    <>
      <section
        className={styles.hero}
        style={
          {
            "--sc-color": scenario.color,
            "--sc-accent": scenario.accent,
          } as React.CSSProperties
        }
      >
        <div className={styles.container}>
          <div className={styles.crumb}>
            <Link href="/training" className={styles.crumbLink}>
              ← Training Console
            </Link>
            <span className={styles.crumbCurrent}>{scenario.number} · {scenario.name}</span>
          </div>

          <div className={styles.heroBody}>
            <Reveal>
              <div className={styles.heroMeta}>
                <span className={styles.metaNum}>{scenario.number}</span>
                <span className={styles.metaDiff}>{scenario.difficulty}</span>
                <span className={styles.metaDur}>{scenario.duration_minutes} min</span>
              </div>
            </Reveal>

            <Reveal delay={0.05}>
              <h1 className={styles.title}>
                {scenario.name}
                <span className={styles.titleZh}>{scenario.name_zh}</span>
              </h1>
            </Reveal>

            <Reveal delay={0.1}>
              <p className={styles.tagline}>{scenario.tagline}</p>
            </Reveal>

            <Reveal delay={0.15}>
              <div className={styles.ctaRow}>
                <Link href={`/simulator/${scenario.slug}`} className={styles.ctaPrimary}>
                  Launch simulator
                  <span className={styles.ctaArrow} aria-hidden="true">→</span>
                </Link>
                <Link href="/training" className={styles.ctaSecondary}>
                  ← All scenarios
                </Link>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <section className={styles.body}>
        <div className={styles.container}>
          <div className={styles.grid}>
            <Reveal>
              <article className={styles.objectives}>
                <h2 className={styles.sectionTitle}>Objectives</h2>
                <ol className={styles.objList}>
                  {scenario.objectives.map((o, i) => (
                    <li key={i} className={styles.objItem}>
                      <span className={styles.objIndex}>
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <span className={styles.objText}>{o}</span>
                    </li>
                  ))}
                </ol>
                <div className={styles.objNote}>
                  <span className={styles.objNoteLabel}>ZH</span>
                  <ol className={styles.objZh}>
                    {scenario.objectives_zh.map((o, i) => (
                      <li key={i}>{o}</li>
                    ))}
                  </ol>
                </div>
              </article>
            </Reveal>

            <Reveal delay={0.1}>
              <aside className={styles.spec}>
                <h2 className={styles.sectionTitle}>Flight envelope</h2>
                <dl className={styles.specList}>
                  <div className={styles.specRow}>
                    <dt>Max altitude</dt>
                    <dd>{(scenario.metrics as any).max_altitude_m} m AGL</dd>
                  </div>
                  <div className={styles.specRow}>
                    <dt>Wind ceiling</dt>
                    <dd>{(scenario.metrics as any).wind_m_s} m/s</dd>
                  </div>
                  <div className={styles.specRow}>
                    <dt>GPS quality</dt>
                    <dd className={styles.specCap}>{(scenario.metrics as any).gps_quality}</dd>
                  </div>
                  <div className={styles.specRow}>
                    <dt>Duration</dt>
                    <dd>{scenario.duration_minutes} minutes</dd>
                  </div>
                  <div className={styles.specRow}>
                    <dt>Difficulty</dt>
                    <dd className={styles.specCap}>{scenario.difficulty}</dd>
                  </div>
                </dl>

                <div className={styles.diagram} aria-hidden="true">
                  <svg viewBox="0 0 200 120" preserveAspectRatio="xMidYMid meet">
                    <defs>
                      <pattern id="diag-grid" width="20" height="20" patternUnits="userSpaceOnUse">
                        <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(26,26,24,0.08)" strokeWidth="0.5" />
                      </pattern>
                    </defs>
                    <rect width="200" height="120" fill="url(#diag-grid)" />
                    <circle cx="100" cy="60" r="46" fill="none" stroke="var(--ink)" strokeWidth="1" />
                    <circle cx="100" cy="60" r="36" fill="none" stroke="var(--ash-500)" strokeWidth="1" />
                    <circle cx="100" cy="60" r="20" fill="none" stroke="var(--ink)" strokeWidth="1" />
                    <line x1="100" y1="14" x2="100" y2="106" stroke="var(--ash-300)" strokeWidth="0.5" />
                    <line x1="54" y1="60" x2="146" y2="60" stroke="var(--ash-300)" strokeWidth="0.5" />
                    <text x="100" y="10" fontFamily="JetBrains Mono" fontSize="6" fill="var(--ash-500)" textAnchor="middle" letterSpacing="0.2">AGL · 100%</text>
                    <text x="100" y="118" fontFamily="JetBrains Mono" fontSize="6" fill="var(--ash-500)" textAnchor="middle" letterSpacing="0.2">GND · 0%</text>
                  </svg>
                </div>
              </aside>
            </Reveal>
          </div>
        </div>
      </section>
    </>
  );
}