"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getScenario } from "@/lib/scenarios";
import { api } from "@/lib/api";
import styles from "./Simulator.module.css";

type Status =
  | "connecting"
  | "no_signal"
  | "running"
  | "hovering"
  | "landed"
  | "link_loss"
  | "disconnected";

type Telemetry = {
  lat: number;
  lon: number;
  alt: number;
  vx: number;
  vy: number;
  vz: number;
  battery: number;
  link_quality: number;
};

type ObjectiveState = {
  id: string;
  label: string;
  status: "pending" | "active" | "satisfied" | "failed";
  progress: number;
};

const FALLBACK_OBJECTIVES = [
  { id: "01", label: "Take off & reach cruise altitude", status: "pending" as const, progress: 0 },
  { id: "02", label: "Execute primary manoeuvre", status: "pending" as const, progress: 0 },
  { id: "03", label: "Hold / land / return home", status: "pending" as const, progress: 0 },
];

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ?? "http://localhost:8000";

export default function SimulatorPage() {
  const router = useRouter();
  const params = useParams<{ slug: string }>();
  const scenario = params.slug ? getScenario(params.slug) : undefined;

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const frameCountRef = useRef(0);
  const lastFrameTimeRef = useRef(performance.now());
  const [fps, setFps] = useState(0);

  const [status, setStatus] = useState<Status>("connecting");
  const [airsimAvailable, setAirsimAvailable] = useState(false);
  const [telemetry, setTelemetry] = useState<Telemetry>({
    lat: 0, lon: 0, alt: 0, vx: 0, vy: 0, vz: 0, battery: 0, link_quality: 0,
  });
  const [objectives, setObjectives] = useState<ObjectiveState[]>(FALLBACK_OBJECTIVES);
  const [score, setScore] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const armedRef = useRef(false);
  const flyingRef = useRef(false);
  const startedAtRef = useRef<number | null>(null);

  // ── Connect to backend WS ─────────────────────────────────────────
  useEffect(() => {
    if (!scenario) return;
    const wsUrl = `${API_BASE.replace(/^http/, "ws")}/api/sim/ws/${scenario.slug}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setStatus("connecting");
    ws.onmessage = (ev) => {
      if (typeof ev.data === "string") {
        try {
          const msg = JSON.parse(ev.data);
          handleServerMessage(msg);
        } catch {}
      } else if (ev.data instanceof Blob) {
        drawBinaryFrame(ev.data);
      } else if (ev.data instanceof ArrayBuffer) {
        drawBinaryFrame(new Blob([ev.data], { type: "image/jpeg" }));
      }
    };
    ws.onclose = () => setStatus("disconnected");
    ws.onerror = () => setStatus("disconnected");

    return () => {
      try { ws.close(); } catch {}
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario?.slug]);

  // ── Mission timer ─────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => {
      if (startedAtRef.current) {
        setElapsed(Math.floor((performance.now() - startedAtRef.current) / 1000));
      }
    }, 250);
    return () => clearInterval(id);
  }, []);

  // ── Keyboard controls ─────────────────────────────────────────────
  useEffect(() => {
    const pressed = new Set<string>();
    const tick = () => {
      const vx = (pressed.has("w") ? 1 : 0) - (pressed.has("s") ? 1 : 0);
      const vy = (pressed.has("d") ? 1 : 0) - (pressed.has("a") ? 1 : 0);
      const vz = (pressed.has("shift") ? 1 : 0) - (pressed.has(" ") ? 1 : 0);
      const yaw = (pressed.has("e") ? 1 : 0) - (pressed.has("q") ? 1 : 0);
      if (vx || vy || vz || yaw) {
        sendCmd({ action: "velocity", vx: vx * 5, vy: vy * 5, vz: vz * 2, yaw: yaw * 30 });
      }
      requestAnimationFrame(tick);
    };
    const id = requestAnimationFrame(tick);
    const onDown = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase();
      pressed.add(k);
      if (k === "r") sendCmd({ action: "rtl" });
      if (k === "x") sendCmd({ action: "land" });
    };
    const onUp = (e: KeyboardEvent) => pressed.delete(e.key.toLowerCase());
    window.addEventListener("keydown", onDown);
    window.addEventListener("keyup", onUp);
    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener("keydown", onDown);
      window.removeEventListener("keyup", onUp);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!scenario) {
    return (
      <div className={styles.shell}>
        <div className={styles.launchOverlay}>
          <div className={styles.launchCard}>
            <h1 className={styles.launchTitle}>Scenario not found</h1>
            <p className={styles.launchCopy}>
              The slug <code>{params.slug}</code> does not match any registered training scenario.
            </p>
            <Link href="/training" className={styles.launchBtn}>
              Back to scenarios <span className={styles.launchArrow}>→</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  function handleServerMessage(msg: any) {
    switch (msg.type) {
      case "hello":
        setAirsimAvailable(!!msg.airsim_available);
        if (!msg.airsim_available) setStatus("no_signal");
        break;
      case "telemetry":
        setTelemetry((prev) => ({
          ...prev,
          lat: msg.lat ?? prev.lat,
          lon: msg.lon ?? prev.lon,
          alt: msg.alt ?? prev.alt,
          vx: msg.vx ?? prev.vx,
          vy: msg.vy ?? prev.vy,
          vz: msg.vz ?? prev.vz,
          battery: msg.battery ?? prev.battery,
          link_quality: msg.link_quality ?? prev.link_quality,
        }));
        if (status === "connecting" && airsimAvailable) setStatus("running");
        if (msg.alt > 0.5) {
          if (startedAtRef.current === null) startedAtRef.current = performance.now();
          flyingRef.current = true;
        }
        break;
      case "no_signal":
        setStatus("no_signal");
        break;
      case "status":
        setStatus(msg.state);
        break;
      case "disconnected":
        setStatus("disconnected");
        break;
      case "objective":
        setObjectives((curr) =>
          curr.map((o) => (o.id === msg.id ? { ...o, status: msg.status, progress: msg.progress } : o)),
        );
        if (msg.status === "satisfied") setScore((s) => s + 100);
        break;
    }
  }

  function drawBinaryFrame(blob: Blob) {
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      if (canvas.width !== img.width) canvas.width = img.width;
      if (canvas.height !== img.height) canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      frameCountRef.current += 1;
      const now = performance.now();
      if (now - lastFrameTimeRef.current > 1000) {
        setFps(frameCountRef.current);
        frameCountRef.current = 0;
        lastFrameTimeRef.current = now;
      }
    };
    img.src = url;
  }

  function sendCmd(cmd: Record<string, unknown>) {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "cmd", ...cmd }));
    if (cmd.action === "arm") armedRef.current = true;
    if (cmd.action === "land") flyingRef.current = false;
  }

  function completeMission() {
    if (!scenario) return;
    setStatus("landed");
    const duration = Math.floor((performance.now() - (startedAtRef.current ?? performance.now())) / 1000);
    api.saveProgress(scenario.slug, {
      score: score + Math.max(0, 500 - elapsed),
      duration_seconds: duration,
      completed: true,
    }).catch(() => {});
    startedAtRef.current = null;
  }

  return (
    <div className={styles.shell} style={{ "--sc-accent": scenario.accent } as React.CSSProperties}>
      <div className={styles.topbar}>
        <div className={styles.topbarLeft}>
          <Link href="/training" className={styles.back}>← Training</Link>
          <span className={styles.divider} />
          <span className={styles.scenarioId}>{scenario.slug.toUpperCase()}</span>
          <span className={styles.scenarioMeta}>{scenario.name}</span>
        </div>
        <div className={styles.topbarRight}>
          <span data-status={status} className={styles.statusBadge}>
            {status.toUpperCase().replace("_", " ")}
          </span>
          <span className={styles.divider} />
          <span className={styles.fps}>{fps} fps</span>
          <button
            className={armedRef.current ? styles.btnPrimary : styles.btn}
            onClick={() => sendCmd({ action: "arm" })}
          >
            {armedRef.current ? "ARMED" : "ARM"}
          </button>
          <button
            className={flyingRef.current ? styles.btnPrimary : styles.btn}
            onClick={() => sendCmd({ action: flyingRef.current ? "land" : "takeoff" })}
          >
            {flyingRef.current ? "LAND" : "TAKEOFF"}
          </button>
          <button className={styles.btn} onClick={() => sendCmd({ action: "rtl" })}>RTL</button>
          <button className={styles.btnPrimary} onClick={completeMission}>END</button>
        </div>
      </div>

      <div className={styles.stage}>
        {/* Primary viewport: live image stream from AirSim */}
        <canvas ref={canvasRef} className={styles.viewport} />

        {/* When AirSim is not reachable, show a clear standby state */}
        {!airsimAvailable && (
          <div className={styles.standbyOverlay}>
            <div className={styles.standbyCard}>
              <div className={styles.standbyPulse} />
              <span className={styles.standbyLabel}>No Signal</span>
              <h2 className={styles.standbyTitle}>AirSim Bridge Standby</h2>
              <p className={styles.standbyCopy}>
                Live image transmission is the canonical view for this scenario.
                The simulator will populate this viewport as soon as the AirSim
                client at <code>{API_BASE.replace(/^http/, "ws")}/api/sim/ws/{scenario.slug}</code>
                {" "}begins streaming frames.
              </p>
              <div className={styles.standbyGrid}>
                <div className={styles.standbyHint}>
                  <span className={styles.standbyHintLabel}>Endpoint</span>
                  <code className={styles.standbyHintCode}>ws://localhost:8000/api/sim/ws/{scenario.slug}</code>
                </div>
                <div className={styles.standbyHint}>
                  <span className={styles.standbyHintLabel}>AirSim default</span>
                  <code className={styles.standbyHintCode}>127.0.0.1:41451</code>
                </div>
                <div className={styles.standbyHint}>
                  <span className={styles.standbyHintLabel}>Protocol</span>
                  <code className={styles.standbyHintCode}>JPEG binary + JSON telemetry</code>
                </div>
              </div>
              <div className={styles.standbyActions}>
                <button className={styles.btn} onClick={() => api.simStatus().then((s) => setAirsimAvailable(s.airsim_available))}>
                  Re-probe
                </button>
                <button className={styles.btn} onClick={() => router.push("/training")}>
                  Back to scenarios
                </button>
              </div>
            </div>
          </div>
        )}

        {/* HUD overlay (visible when stream is active) */}
        {airsimAvailable && (
          <>
            <div className={styles.hudTop}>
              <div className={styles.hudCard}>
                <span className={styles.hudLabel}>Altitude</span>
                <span className={styles.hudValue}>{telemetry.alt.toFixed(1)}</span>
                <span className={styles.hudUnit}>m AGL</span>
              </div>
              <div className={styles.hudCard}>
                <span className={styles.hudLabel}>Ground Speed</span>
                <span className={styles.hudValue}>
                  {Math.sqrt(telemetry.vx ** 2 + telemetry.vy ** 2).toFixed(1)}
                </span>
                <span className={styles.hudUnit}>m/s</span>
              </div>
              <div className={styles.hudCard}>
                <span className={styles.hudLabel}>Battery</span>
                <span className={styles.hudValue}>{telemetry.battery.toFixed(0)}</span>
                <span className={styles.hudUnit}>%</span>
              </div>
              <div className={styles.hudCard}>
                <span className={styles.hudLabel}>Link</span>
                <span className={styles.hudValue}>{(telemetry.link_quality * 100).toFixed(0)}</span>
                <span className={styles.hudUnit}>%</span>
              </div>
              <div className={styles.hudCard}>
                <span className={styles.hudLabel}>Lat / Lon</span>
                <span className={styles.hudValue} style={{ fontSize: 18 }}>
                  {telemetry.lat.toFixed(4)}, {telemetry.lon.toFixed(4)}
                </span>
              </div>
            </div>

            <div className={styles.hudBottom}>
              {objectives.map((o, i) => (
                <div key={o.id} className={styles.objectiveCard} data-status={o.status}>
                  <div className={styles.objectiveHead}>
                    <span className={styles.objectiveNum}>{o.id}</span>
                    <span className={styles.objectiveStatus}>{o.status.toUpperCase()}</span>
                  </div>
                  <span className={styles.objectiveLabel}>{o.label}</span>
                  <div className={styles.progressTrack}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${Math.min(100, o.progress * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.scoreCard}>
              <div className={styles.scoreRow}>
                <span className={styles.scoreLabel}>Score</span>
                <span className={styles.scoreValue}>{score}</span>
              </div>
              <div className={styles.scoreRow}>
                <span className={styles.scoreLabel}>Mission Time</span>
                <span className={styles.scoreValue}>
                  {String(Math.floor(elapsed / 60)).padStart(2, "0")}:
                  {String(elapsed % 60).padStart(2, "0")}
                </span>
              </div>
            </div>
          </>
        )}

        <div className={styles.controls}>
          <span className={styles.controlsLabel}>Controls</span>
          <span className={styles.controlsRow}><kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> Strafe</span>
          <span className={styles.controlsRow}><kbd>Space</kbd>/<kbd>⇧</kbd> Altitude</span>
          <span className={styles.controlsRow}><kbd>Q</kbd>/<kbd>E</kbd> Yaw</span>
          <span className={styles.controlsRow}><kbd>R</kbd> RTL</span>
          <span className={styles.controlsRow}><kbd>X</kbd> Land</span>
        </div>
      </div>

      {/* Local CSS additions */}
      <style jsx>{`
        .viewport {
          width: 100%;
          height: 100%;
          display: block;
          background: #1A1A18;
          object-fit: contain;
        }
        .statusBadge {
          font-family: var(--font-mono);
          font-size: 11px;
          letter-spacing: 0.18em;
          padding: 4px 8px;
          border: 1px solid var(--ash-700);
          color: var(--ash-300);
        }
        .statusBadge[data-status="running"] {
          background: var(--sc-accent);
          color: var(--ink);
          border-color: var(--sc-accent);
        }
        .statusBadge[data-status="no_signal"],
        .statusBadge[data-status="disconnected"],
        .statusBadge[data-status="link_loss"] {
          background: var(--signal, #D94F1E);
          color: var(--paper);
          border-color: transparent;
        }
        .fps {
          font-family: var(--font-mono);
          font-size: 11px;
          letter-spacing: 0.18em;
          color: var(--ash-300);
        }
      `}</style>
    </div>
  );
}