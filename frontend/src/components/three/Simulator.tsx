"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { getToken } from "@/lib/auth";
import { api } from "@/lib/api";
import type { ScenarioMeta } from "@/lib/scenarios";
import styles from "./Simulator.module.css";

const Scene = dynamic(() => import("./Scene").then((m) => m.Scene), { ssr: false });

type SimState = {
  alt: number;
  vx: number;
  vy: number;
  vz: number;
  yaw: number;
  battery: number;
  status: "running" | "landed" | "aborted";
  score: number;
  duration: number;
};

const INITIAL: SimState = {
  alt: 0,
  vx: 0, vy: 0, vz: 0, yaw: 0,
  battery: 100,
  status: "landed",
  score: 0,
  duration: 0,
};

export function Simulator({ scenario }: { scenario: ScenarioMeta }) {
  const [state, setState] = useState<SimState>(INITIAL);
  const [paused, setPaused] = useState(true);
  const [scoreSaved, setScoreSaved] = useState(false);
  const tickRef = useRef<number | null>(null);

  // Keyboard control
  useEffect(() => {
    const keys: Record<string, boolean> = {};
    const onDown = (e: KeyboardEvent) => (keys[e.key.toLowerCase()] = true);
    const onUp = (e: KeyboardEvent) => (keys[e.key.toLowerCase()] = false);
    window.addEventListener("keydown", onDown);
    window.addEventListener("keyup", onUp);

    const interval = window.setInterval(() => {
      if (paused) return;
      setState((s) => {
        let { alt, vx, vy, vz, yaw, battery, status, duration } = s;
        const accel = 0.08;
        if (keys["w"]) vy += accel;
        if (keys["s"]) vy -= accel;
        if (keys["a"]) vx -= accel;
        if (keys["d"]) vx += accel;
        if (keys[" "]) vz -= accel; // ascend
        if (keys["shift"]) vz += accel; // descend
        if (keys["q"]) yaw -= 1.4;
        if (keys["e"]) yaw += 1.4;
        if (keys["r"]) { vx = 0; vy = 0; vz = 0; yaw = 0; }

        // Damping
        vx *= 0.94; vy *= 0.94; vz *= 0.94;

        // Update derived
        alt = Math.max(0, alt - vz * 0.5);
        battery = Math.max(0, battery - 0.012);
        duration += 0.05;

        const score = Math.round(
          Math.max(0, alt) * 5 +
          (Math.abs(vx) + Math.abs(vy) + Math.abs(vz)) * 50 +
          duration * 0.5,
        );

        return { alt, vx, vy, vz, yaw, battery, status: status === "landed" && alt > 0.5 ? "running" : status, score, duration };
      });
    }, 50);

    return () => {
      window.removeEventListener("keydown", onDown);
      window.removeEventListener("keyup", onUp);
      window.clearInterval(interval);
    };
  }, [paused]);

  // Save progress on land / abort
  const persist = async () => {
    if (scoreSaved) return;
    const token = getToken();
    if (!token) return;
    try {
      await api.saveProgress(scenario.slug, {
        score: state.score,
        duration_seconds: Math.round(state.duration),
        completed: state.score > 100,
      });
      setScoreSaved(true);
    } catch {
      /* ignore */
    }
  };

  const startFlight = () => {
    setPaused(false);
    setState((s) => ({ ...s, status: "running", alt: Math.max(s.alt, 0.4) }));
  };

  const land = async () => {
    setPaused(true);
    setState((s) => ({ ...s, status: "landed" }));
    await persist();
  };

  const reset = () => {
    setState(INITIAL);
    setPaused(true);
    setScoreSaved(false);
  };

  return (
    <div
      className={styles.shell}
      style={
        {
          "--sc-color": scenario.color,
          "--sc-accent": scenario.accent,
        } as React.CSSProperties
      }
    >
      <header className={styles.topbar}>
        <div className={styles.topbarLeft}>
          <Link href={`/training/${scenario.slug}`} className={styles.back}>
            ← {scenario.name}
          </Link>
          <span className={styles.divider} />
          <span className={styles.scenarioId}>{scenario.number}</span>
          <span className={styles.scenarioMeta}>{scenario.difficulty}</span>
        </div>
        <div className={styles.topbarRight}>
          <button onClick={() => setPaused((p) => !p)} className={styles.btn}>
            {paused ? "Resume" : "Pause"}
          </button>
          <button onClick={reset} className={styles.btn}>Reset</button>
          <button onClick={land} className={styles.btnPrimary}>Land & save</button>
        </div>
      </header>

      <div className={styles.stage}>
        <Scene scenario={scenario} state={state} />

        {/* HUD overlay */}
        <div className={styles.hudTop}>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>ALT</span>
            <span className={styles.hudValue}>{state.alt.toFixed(1)}</span>
            <span className={styles.hudUnit}>m AGL</span>
          </div>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>VEL</span>
            <span className={styles.hudValue}>{Math.hypot(state.vx, state.vy, state.vz).toFixed(1)}</span>
            <span className={styles.hudUnit}>m/s</span>
          </div>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>YAW</span>
            <span className={styles.hudValue}>{((state.yaw * 180) / Math.PI % 360).toFixed(0)}</span>
            <span className={styles.hudUnit}>deg</span>
          </div>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>BAT</span>
            <span className={styles.hudValue}>{state.battery.toFixed(0)}</span>
            <span className={styles.hudUnit}>%</span>
          </div>
        </div>

        <div className={styles.hudBottom}>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>SCORE</span>
            <span className={styles.hudBig}>{state.score.toLocaleString()}</span>
          </div>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>MISSION TIME</span>
            <span className={styles.hudBig}>{formatTime(state.duration)}</span>
          </div>
          <div className={styles.hudCard}>
            <span className={styles.hudLabel}>STATUS</span>
            <span className={styles.hudBig} data-status={state.status}>
              {state.status === "running" ? "IN FLIGHT" : state.status === "landed" ? "LANDED" : "ABORTED"}
            </span>
          </div>
        </div>

        {/* Controls hint */}
        <div className={styles.controls}>
          <span className={styles.controlsLabel}>CONTROLS</span>
          <div className={styles.controlsRow}>
            <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> <span>Translate</span>
          </div>
          <div className={styles.controlsRow}>
            <kbd>SPACE</kbd> <span>Ascend</span>
            <span className={styles.controlsDivider} />
            <kbd>SHIFT</kbd> <span>Descend</span>
          </div>
          <div className={styles.controlsRow}>
            <kbd>Q</kbd><kbd>E</kbd> <span>Yaw</span>
            <span className={styles.controlsDivider} />
            <kbd>R</kbd> <span>Reset attitude</span>
          </div>
        </div>

        {paused && state.status === "landed" && state.duration === 0 && (
          <div className={styles.launchOverlay}>
            <div className={styles.launchCard}>
              <h2 className={styles.launchTitle}>{scenario.name}</h2>
              <p className={styles.launchCopy}>{scenario.tagline}</p>
              <button onClick={startFlight} className={styles.launchBtn}>
                <span>Begin scenario</span>
                <span className={styles.launchArrow}>→</span>
              </button>
              <p className={styles.launchMeta}>
                {scenario.duration_minutes} min · {scenario.objectives.length} objectives · {scenario.difficulty}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}