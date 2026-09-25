"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ProgressEntry } from "@/lib/types";
import { SCENARIOS } from "@/lib/scenarios";
import styles from "./page.module.css";

export default function ProgressPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<ProgressEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    api
      .myProgress()
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [router]);

  const totalScore = entries.reduce((acc, e) => acc + e.best_score, 0);
  const completed = entries.filter((e) => e.completed).length;

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.eyebrowRow}>
          <span>00</span>
          <span>Training Progress</span>
          <span>Per-scenario record</span>
          <span>2026 · Q3</span>
        </div>

        <div className={styles.heroRow}>
          <div>
            <h1 className={styles.title}>Your training record.</h1>
            <p className={styles.lede}>
              Cumulative scores, attempts, and best durations across all six
              scenarios. Progress is saved locally on the simulator page
              and synced to the platform once you land.
            </p>
          </div>

          <div className={styles.statBox}>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>Scenarios completed</span>
              <span className={styles.statValue}>{completed} / 6</span>
            </div>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>Cumulative score</span>
              <span className={styles.statValue}>{totalScore.toLocaleString()}</span>
            </div>
            <div className={styles.statRow}>
              <span className={styles.statLabel}>Total attempts</span>
              <span className={styles.statValue}>
                {entries.reduce((a, e) => a + e.attempts, 0)}
              </span>
            </div>
          </div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>#</th>
                <th>Scenario</th>
                <th>Best score</th>
                <th>Best time</th>
                <th>Attempts</th>
                <th>Status</th>
                <th>Last played</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {SCENARIOS.map((s) => {
                const e = entries.find((x) => x.scenario_slug === s.slug);
                return (
                  <tr key={s.slug}>
                    <td className={styles.cellNum}>{s.number}</td>
                    <td>
                      <div className={styles.scenCell}>
                        <span className={styles.scenName}>{s.name}</span>
                        <span className={styles.scenZh}>{s.name_zh}</span>
                      </div>
                    </td>
                    <td className={styles.cellMono}>{e?.best_score?.toLocaleString() ?? "—"}</td>
                    <td className={styles.cellMono}>
                      {e?.best_duration_seconds ? formatTime(e.best_duration_seconds) : "—"}
                    </td>
                    <td className={styles.cellMono}>{e?.attempts ?? 0}</td>
                    <td>
                      <span className={e?.completed ? styles.statusOn : styles.statusOff}>
                        {e?.completed ? "Completed" : "—"}
                      </span>
                    </td>
                    <td className={styles.cellMono}>{e?.last_played?.slice(0, 10) ?? "—"}</td>
                    <td className={styles.cellAction}>
                      <a href={`/simulator/${s.slug}`} className={styles.actionBtn}>
                        Open →
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, "0")}`;
}