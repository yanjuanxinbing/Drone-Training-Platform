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

/* Objectives now come from the backend. `hello` carries the full task list
   (built from the scenario's `tasks` rules) and `objective` messages patch
   individual entries as the rule engine evaluates them. The server is the
   single source of truth — a hardcoded placeholder list would drift out of
   sync with the actual mission, which is exactly what the old
   FALLBACK_OBJECTIVES did. */
type ServerObjective = {
  id: string;
  label: string;
  status: "pending" | "active" | "satisfied" | "failed";
  progress: number;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ?? "http://localhost:8000";

export default function SimulatorPage() {
  const router = useRouter();
  const params = useParams<{ slug: string }>();
  const scenario = params.slug ? getScenario(params.slug) : undefined;

  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const [status, setStatus] = useState<Status>("connecting");
  const [pixelStreamingUrl, setPixelStreamingUrl] = useState<string | null>(null);
  const [streamReady, setStreamReady] = useState(false);
  const [iframeNonce, setIframeNonce] = useState(0); // bump to force iframe reload
  const [streamClickable, setStreamClickable] = useState(true); // mirrors static/app.js: iframe receives the first click so PS Player's "Click to start" overlay gets it; after WebRTC stabilises we switch to pointer-events:none so the page owns the cursor.
  const [telemetry, setTelemetry] = useState<Telemetry>({
    lat: 0, lon: 0, alt: 0, vx: 0, vy: 0, vz: 0, battery: 0, link_quality: 0,
  });
  // Seeded from the scenario's own text so the checklist is meaningful
  // before the WebSocket connects, then replaced wholesale by the server's
  // `hello` payload as soon as it arrives.
  const [objectives, setObjectives] = useState<ObjectiveState[]>(() =>
    scenario
      ? scenario.objectives.map((label, i) => ({
          id: String(i + 1).padStart(2, "0"),
          label,
          status: "pending" as const,
          progress: 0,
        }))
      : [],
  );
  // Authoritative score. Computed server-side by the rule engine, which
  // weights each task by `points`; the client used to invent its own
  // (+100 per satisfied message) and double-counted repeats.
  const [score, setScore] = useState(0);
  const [missionComplete, setMissionComplete] = useState(false);
  const [saveError, setSaveError] = useState(false);
  // Live seconds while flying; shown in the HUD as a running clock.
  const [elapsed, setElapsed] = useState(0);
  // Final duration, captured once at completion. Held separately from
  // `elapsed` because the 250 ms interval keeps running and would otherwise
  // keep advancing the number the completion panel is showing.
  const [finalDuration, setFinalDuration] = useState<number | null>(null);
  const armedRef = useRef(false);
  const flyingRef = useRef(false);
  const startedAtRef = useRef<number | null>(null);
  // Guards `completeMission` so the 10 Hz stream can't fire it repeatedly
  // and inflate the recorded attempt/score.
  const missionSavedRef = useRef(false);

  // ── Fetch Pixel Streaming config ──────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    api.streamConfig()
      .then((cfg) => {
        if (cancelled) return;
        setPixelStreamingUrl(cfg.pixel_streaming_url);
      })
      .catch(() => {
        // Leave pixelStreamingUrl null → standby overlay takes over.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // ── Connect to backend WS (telemetry + commands only) ─────────────
  useEffect(() => {
    if (!scenario) return;
    const wsUrl = `${API_BASE.replace(/^http/, "ws")}/api/sim/ws/${scenario.slug}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setStatus("connecting");
    ws.onmessage = (ev) => {
      if (typeof ev.data !== "string") return;
      try {
        const msg = JSON.parse(ev.data);
        handleServerMessage(msg);
      } catch {
        /* ignore malformed frames */
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

  // Reset stream-readiness when URL changes (user reprobes)
  useEffect(() => {
    setStreamReady(false);
  }, [pixelStreamingUrl, iframeNonce]);

  // ── Mission timer ─────────────────────────────────────────────────
  // Runs while flying only. On completion the value is frozen in
  // `finalDuration` and this loop stops contributing, so the readout the
  // user is looking at stops changing.
  useEffect(() => {
    const id = setInterval(() => {
      if (startedAtRef.current !== null) {
        setElapsed(Math.floor((performance.now() - startedAtRef.current) / 1000));
      }
    }, 250);
    return () => clearInterval(id);
  }, []);

  // ── Gamepad controls ──────────────────────────────────────────────
  // Mirrors the control scheme in `static/app.js` at the repo root:
  //   LB (held)            — safety gate; sticks + A/B/Y only work while held
  //   Left stick X (axis0) — yaw rate
  //   Left stick Y (axis1) — altitude (vz)
  //   Right stick X (axis2)— strafe left/right (vy)
  //   Right stick Y (axis3)— strafe forward/back (vx, negated)
  //   A (btn 0)            — arm → takeoff state machine
  //   B (btn 1)            — land → disarm state machine
  //   Y (btn 3)            — emergency (kill motors)
  const [gamepadName, setGamepadName] = useState<string | null>(null);
  const gamepadIndexRef = useRef<number | null>(null);
  const prevButtonsRef = useRef<boolean[]>([]);

  useEffect(() => {
    const HSPD = 4.0;
    const VSPD = 2.5;
    const YAW_SPD = 45;
    const DEADZONE = 0.12;
    const BTN_A = 0;
    const BTN_B = 1;
    const BTN_Y = 3;
    const BTN_LB = 4;

    const applyAxis = (value: number, scale: number) =>
      Math.abs(value) < DEADZONE ? 0 : value * scale;

    const isPressed = (gp: Gamepad, idx: number) =>
      !!(gp.buttons[idx] && gp.buttons[idx].pressed);

    const readGamepad = () => {
      const gps = navigator.getGamepads ? navigator.getGamepads() : [];
      let gp: Gamepad | null = null;
      if (gamepadIndexRef.current !== null) gp = gps[gamepadIndexRef.current] ?? null;
      if (!gp || !gp.connected) {
        for (let i = 0; i < gps.length; i++) {
          const candidate = gps[i];
          if (candidate && candidate.connected) {
            gp = candidate;
            gamepadIndexRef.current = i;
            setGamepadName(((candidate.id || "Gamepad")).replace(/\s*\(.*?\)\s*/g, "").trim());
            break;
          }
        }
      }
      if (!gp) return;

      const axes = gp.axes || [];
      const lbHeld = isPressed(gp, BTN_LB);
      const aNow = isPressed(gp, BTN_A);
      const bNow = isPressed(gp, BTN_B);
      const yNow = isPressed(gp, BTN_Y);

      if (lbHeld) {
        const yaw = applyAxis(axes[0] || 0, YAW_SPD);
        const vz = applyAxis(axes[1] || 0, VSPD);
        const vy = applyAxis(axes[2] || 0, HSPD);
        const vx = applyAxis(-(axes[3] || 0), HSPD);
        if (vx || vy || vz || yaw) {
          sendCmd({ action: "velocity", vx, vy, vz, yaw });
        }
        if (yNow && !prevButtonsRef.current[BTN_Y]) emergencyStop();
        if (aNow && !prevButtonsRef.current[BTN_A]) actionA();
        if (bNow && !prevButtonsRef.current[BTN_B]) actionB();
      } else {
        // Safety gate closed — sticks return to zero so the drone never
        // drifts after the operator lets go of LB.
        sendCmd({ action: "velocity", vx: 0, vy: 0, vz: 0, yaw: 0 });
      }

      prevButtonsRef.current[BTN_A] = aNow;
      prevButtonsRef.current[BTN_B] = bNow;
      prevButtonsRef.current[BTN_Y] = yNow;
    };

    const rafLoop = () => {
      readGamepad();
      requestAnimationFrame(rafLoop);
    };

    const onConnect = (e: GamepadEvent) => {
      gamepadIndexRef.current = e.gamepad.index;
      setGamepadName(e.gamepad.id.replace(/\s*\(.*?\)\s*/g, "").trim());
    };
    const onDisconnect = (e: GamepadEvent) => {
      if (gamepadIndexRef.current === e.gamepad.index) {
        gamepadIndexRef.current = null;
        setGamepadName(null);
        // Lost link mid-flight: land; if just armed, disarm.
        if (flyingRef.current) sendCmd({ action: "land" });
        else if (armedRef.current) sendCmd({ action: "disarm" });
      }
    };

    window.addEventListener("gamepadconnected", onConnect);
    window.addEventListener("gamepaddisconnected", onDisconnect);
    const id = requestAnimationFrame(rafLoop);
    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener("gamepadconnected", onConnect);
      window.removeEventListener("gamepaddisconnected", onDisconnect);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Gamepad action helpers (mirror static/app.js semantics) ──────
  async function actionA() {
    if (!armedRef.current && !flyingRef.current) {
      // ARM → send arm cmd, optimistically flag local state so a second
      // tap on A progresses to TAKEOFF without waiting for telemetry round-trip.
      armedRef.current = true;
      sendCmd({ action: "arm" });
    } else if (armedRef.current && !flyingRef.current) {
      flyingRef.current = true;
      sendCmd({ action: "takeoff" });
    }
  }

  async function actionB() {
    if (flyingRef.current) {
      flyingRef.current = false;
      sendCmd({ action: "land" });
    } else if (armedRef.current) {
      armedRef.current = false;
      sendCmd({ action: "disarm" });
    }
  }

  async function emergencyStop() {
    // Gamepad Y = kill motors; bypasses any safety gate.
    flyingRef.current = false;
    armedRef.current = false;
    sendCmd({ action: "emergency" });
  }

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
        if (!msg.airsim_available) setStatus("no_signal");
        // Replace the whole checklist: the server's task ids come from the
        // scenario's `tasks` rules and won't line up with the placeholder ids
        // seeded from `scenario.objectives`.
        if (Array.isArray(msg.objectives) && msg.objectives.length) {
          setObjectives(msg.objectives as ObjectiveState[]);
        }
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
        if (status === "connecting") setStatus("running");
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
        setObjectives((curr) => {
          const i = curr.findIndex((o) => o.id === msg.id);
          if (i === -1) {
            // A task the server knows about but we don't yet (e.g. it arrived
            // before `hello`). Append rather than drop it.
            return [
              ...curr,
              {
                id: msg.id,
                label: msg.label ?? msg.id,
                status: msg.status,
                progress: msg.progress ?? 0,
              },
            ];
          }
          const next = curr.slice();
          next[i] = { ...next[i], status: msg.status, progress: msg.progress ?? next[i].progress };
          return next;
        });
        // No local scoring here — the server owns it and sends `score`.
        // The old `setScore(s => s + 100)` fired on every repeat message and
        // inflated the total. Completion is likewise signalled by the server
        // via `score` + `completed`, not inferred here.
        break;
      case "score":
        setScore(msg.score ?? 0);
        if (msg.completed && !missionComplete) {
          setMissionComplete(true);
          completeMission(msg.score ?? 0);
        }
        break;
    }
  }

  function reprobeStream() {
    setStreamReady(false);
    setIframeNonce((n) => n + 1);
  }

  function sendCmd(cmd: Record<string, unknown>) {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "cmd", ...cmd }));
    if (cmd.action === "arm") armedRef.current = true;
    if (cmd.action === "land") flyingRef.current = false;
  }

  async function completeMission(finalScore: number) {
    if (!scenario) return;
    // The server sends `score` with completed=true on the same tick the last
    // task is satisfied. Guard so one run records exactly one attempt — the
    // stream can emit further score messages afterwards.
    if (missionSavedRef.current) return;
    missionSavedRef.current = true;

    setStatus("landed");
    const duration = Math.floor(
      (performance.now() - (startedAtRef.current ?? performance.now())) / 1000,
    );
    // Freeze the readout. `elapsed` keeps ticking from the interval, so the
    // displayed value must come from here — previously the panel showed a
    // number that climbed forever after the mission had already ended.
    setFinalDuration(duration);
    setElapsed(duration);
    // `finalScore` is passed in rather than read from state: setScore is
    // async, so the state value here would still be the previous tick's.
    try {
      await api.saveProgress(scenario.slug, {
        score: finalScore,
        duration_seconds: duration,
        completed: true,
      });
    } catch (err) {
      // The old code swallowed this with `.catch(() => {})`, so a signed-out
      // user (the endpoint requires auth) silently lost their result with no
      // indication anything was wrong.
      console.warn("[sim] 保存训练进度失败（可能未登录）", err);
      setSaveError(true);
    }
    // Note: `startedAtRef` is intentionally left intact. Clearing it made the
    // timer stop entirely and lost the anchor needed if the page were reused
    // for another run; the interval is a no-op anyway once the panel is read
    // from `finalDuration`.
  }

  // Map the internal `Status` enum onto the static-style "● AirSim: <state>" badge
// text + colour so the bottom-left HUD matches `static/index.html` / `static/app.js`.
const STATUS_BADGE_TEXT: Record<Status, string> = {
  connecting: "● AirSim: 连接中",
  no_signal: "● AirSim: 未起飞",
  running: "● AirSim: 飞行中",
  hovering: "● AirSim: 悬停",
  landed: "● AirSim: 已降落",
  link_loss: "● AirSim: 链路丢失",
  disconnected: "● AirSim: 失联",
};

/** Seconds → `M:SS` (or `H:MM:SS` past an hour). Fixed-width, never ticks. */
function formatDuration(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
}

function statusBadgeClass(status: Status): string {
  if (status === "running" || status === "hovering") return styles.badgeOk ?? "";
  if (status === "connecting") return styles.badgeFlying ?? "";
  if (status === "no_signal" || status === "landed") return styles.badgeMuted ?? "";
  return styles.badgeErr ?? "";
}

return (
    <div className={styles.shell}>
      {/* Fullscreen UE4.27 Pixel Streaming iframe — mirrors static/index.html.
          The on-screen controls (the "+" toggle, "Kick all other players", and
          the Encoder / WebRTC / Stats / Latency panels) are stripped directly
          inside www/player.html, so the iframe loads the bare URL unchanged. */}
      {pixelStreamingUrl && (
        <iframe
          key={iframeNonce}
          ref={iframeRef}
          src={pixelStreamingUrl}
          className={`${styles.streamFrame} ${streamClickable ? "" : styles.streamPassThrough}`}
          allow="autoplay; microphone; camera; display-capture; xr-spatial-tracking; clipboard-read; clipboard-write"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          tabIndex={-1}
          onLoad={(_) => setStreamReady(true)}
          onError={(_) => setStreamReady(false)}
          onClick={() => {
            if (!streamClickable) return;
            setStreamClickable(false);
          }}
          title={`${scenario.slug.toUpperCase()} · UE4.27 Pixel Streaming`}
        />
      )}

      {/* Standby overlay — shown while UE4.27 + Cirrus aren't reachable */}
      {(!pixelStreamingUrl || !streamReady) && (
        <div className={styles.standbyOverlay}>
          <div className={styles.standbyCard}>
            <div className={styles.standbyPulse} />
            <span className={styles.standbyLabel}>图传未就绪</span>
            <h2 className={styles.standbyTitle}>Pixel Streaming Standby</h2>
            <p className={styles.standbyCopy}>
              Live image transmission is provided by the UE4.27 Pixel Streaming
              Player. Start a UE4.27 build with the Pixel Streaming plugin and
              the Cirrus signalling server, then point it at this page.
              The AirSim flight channel below stays live either way.
            </p>
            <div className={styles.standbyGrid}>
              <div className={styles.standbyHint}>
                <span className={styles.standbyHintLabel}>Player URL</span>
                <code className={styles.standbyHintCode}>{pixelStreamingUrl ?? "未配置"}</code>
              </div>
              <div className={styles.standbyHint}>
                <span className={styles.standbyHintLabel}>Override</span>
                <code className={styles.standbyHintCode}>DRONE_PIXEL_STREAMING_URL</code>
              </div>
              <div className={styles.standbyHint}>
                <span className={styles.standbyHintLabel}>AirSim link</span>
                <code className={styles.standbyHintCode}>ws://localhost:8000/api/sim/ws/{scenario.slug}</code>
              </div>
            </div>
            <div className={styles.standbyActions}>
              <button className={styles.btn} onClick={reprobeStream}>
                Re-probe
              </button>
              <button className={styles.btn} onClick={() => router.push("/training")}>
                Back to scenarios
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating back button — top-left small circle, doesn't block view.
          Mirrors `#back-fab` in static/style.css. */}
      <button
        id="back-fab"
        className={styles.backFab}
        title="返回"
        onClick={() => router.push("/training")}
      >
        ←
      </button>

      {/* Floating status badges — bottom-left, two stacked.
          Mirrors `#hud` / `#conn-badge` / `#gamepad-badge` in static/. */}
      <div id="hud" className={styles.hud}>
        <span className={`${styles.badge} ${statusBadgeClass(status)}`}>
          {STATUS_BADGE_TEXT[status]}
        </span>
        <span
          id="gamepad-badge"
          className={`${styles.gpBadge} ${gamepadName ? styles.gpBadgeOn : styles.gpBadgeOff}`}
        >
          🎮 {gamepadName ?? "未连接手柄"}
        </span>
        {/* Live flight clock. Once the mission completes it switches to the
            frozen final duration, so it and the panel always agree. */}
        {elapsed > 0 && (
          <span className={styles.badge}>
            ⏱ {formatDuration(missionComplete && finalDuration !== null ? finalDuration : elapsed)}
          </span>
        )}
      </div>

      {/* ── Mission panel (top-right) ───────────────────────────────────
          Task list + score, driven entirely by the server's rule engine.
          `pointer-events: none` in CSS so it never steals clicks from the
          Pixel Streaming iframe underneath. */}
      {objectives.length > 0 && (
        <aside className={styles.missionPanel} aria-live="polite">
          <header className={styles.missionHeader}>
            <span className={styles.missionTitle}>训练任务</span>
            <span className={styles.missionScore}>
              {missionComplete ? "✓ " : ""}
              {score}
            </span>
          </header>

          <ol className={styles.objList}>
            {objectives.map((o) => (
              <li key={o.id} className={`${styles.objItem} ${styles[`obj_${o.status}`]}`}>
                <span className={styles.objMark}>
                  {o.status === "satisfied" ? "✓" : o.status === "failed" ? "✕" : o.id}
                </span>
                <span className={styles.objBody}>
                  <span className={styles.objLabel}>{o.label}</span>
                  {o.status === "active" && o.progress > 0 && (
                    <span className={styles.objBar} aria-hidden="true">
                      <span
                        className={styles.objBarFill}
                        style={{ width: `${Math.round(o.progress * 100)}%` }}
                      />
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ol>

          {missionComplete && finalDuration !== null && (
            <p className={styles.missionDone}>
              训练完成 · 用时 {formatDuration(finalDuration)}
              <button className={styles.missionExit} onClick={() => router.push("/account/progress")}>
                查看成绩 →
              </button>
            </p>
          )}

          {saveError && (
            <p className={styles.missionWarn}>进度未能保存，请先登录后再完成训练。</p>
          )}
        </aside>
      )}
    </div>
  );
}