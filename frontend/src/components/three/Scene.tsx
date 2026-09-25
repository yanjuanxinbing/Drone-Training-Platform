"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useRef, useEffect } from "react";
import * as THREE from "three";
import type { ScenarioMeta } from "@/lib/scenarios";
import { Urban } from "./scenarios/Urban";
import { Forest } from "./scenarios/Forest";
import { Indoor } from "./scenarios/Indoor";
import { Mountain } from "./scenarios/Mountain";
import { Coastal } from "./scenarios/Coastal";
import { Industrial } from "./scenarios/Industrial";

type SimState = {
  alt: number;
  vx: number;
  vy: number;
  vz: number;
  yaw: number;
  battery: number;
  status: string;
  score: number;
  duration: number;
};

const SCENARIO_RENDERERS = {
  urban: Urban,
  forest: Forest,
  indoor: Indoor,
  mountain: Mountain,
  coastal: Coastal,
  industrial: Industrial,
} as const;

export function Scene({ scenario, state }: { scenario: ScenarioMeta; state: SimState }) {
  const ScenarioRenderer = SCENARIO_RENDERERS[scenario.slug as keyof typeof SCENARIO_RENDERERS] ?? Urban;

  return (
    <Canvas
      shadows
      camera={{ position: [12, 8, 12], fov: 50, near: 0.1, far: 1000 }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      dpr={[1, 2]}
    >
      <color attach="background" args={[scenario.color === "#FFFFFF" ? "#F4F4F1" : "#1A1A18"]} />
      <fog attach="fog" args={[scenario.color === "#FFFFFF" ? "#F4F4F1" : "#1A1A18", 30, 90]} />

      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 20, 8]} intensity={1.2} castShadow />
      <hemisphereLight args={["#ffffff", scenario.accent, 0.35]} />

      <Suspense fallback={null}>
        <ScenarioRenderer accent={scenario.accent} />
      </Suspense>

      <Drone state={state} accent={scenario.accent} />

      <RigFollow state={state} />
    </Canvas>
  );
}

/* ── Drone — primitive geometry, animated by state ───────────────── */
function Drone({ state, accent }: { state: SimState; accent: string }) {
  const group = useRef<THREE.Group>(null);
  const propellerRefs = useRef<(THREE.Mesh | null)[]>([]);

  useFrame((_, dt) => {
    if (!group.current) return;
    const target = new THREE.Vector3(
      state.vx * 5,
      Math.max(0.4, state.alt + 0.4),
      state.vy * 5,
    );
    group.current.position.lerp(target, Math.min(1, dt * 4));
    group.current.rotation.y = -state.yaw;

    const wobble = Math.sin(performance.now() * 0.01) * 0.02 * (Math.abs(state.vx) + Math.abs(state.vy));
    group.current.rotation.x = wobble;
    group.current.rotation.z = -wobble;

    propellerRefs.current.forEach((p) => p && (p.rotation.y += dt * 40));
  });

  return (
    <group ref={group} position={[0, 0.4, 0]}>
      {/* Body */}
      <mesh castShadow>
        <boxGeometry args={[1.2, 0.18, 1.2]} />
        <meshStandardMaterial color="#1A1A18" />
      </mesh>
      {/* Arms */}
      {[
        [0.6, 0, 0.6],
        [-0.6, 0, -0.6],
        [0.6, 0, -0.6],
        [-0.6, 0, 0.6],
      ].map((pos, i) => (
        <group key={i} position={pos as [number, number, number]}>
          <mesh castShadow>
            <cylinderGeometry args={[0.06, 0.06, 0.6]} />
            <meshStandardMaterial color="#1A1A18" />
          </mesh>
          <mesh
            position={[0, 0.18, 0]}
            ref={(el) => {
              propellerRefs.current[i] = el;
            }}
          >
            <cylinderGeometry args={[0.32, 0.32, 0.02]} />
            <meshStandardMaterial color="#6B6B68" transparent opacity={0.55} />
          </mesh>
          <mesh position={[0, 0.18, 0]}>
            <torusGeometry args={[0.32, 0.01, 4, 16]} />
            <meshStandardMaterial color="#1A1A18" />
          </mesh>
        </group>
      ))}
      {/* Camera dome */}
      <mesh position={[0, -0.18, 0]}>
        <sphereGeometry args={[0.18, 16, 16]} />
        <meshStandardMaterial color="#1A1A18" />
      </mesh>
      {/* Status LED */}
      <mesh position={[0, 0.05, 0.5]}>
        <sphereGeometry args={[0.05, 8, 8]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
      </mesh>
    </group>
  );
}

/* ── Camera that gently follows the drone ───────────────────────── */
function RigFollow({ state }: { state: SimState }) {
  const { camera } = useThree();
  useEffect(() => {
    camera.position.set(6, 4, 6);
    camera.lookAt(0, 0.4, 0);
  }, [camera]);

  useFrame((_, dt) => {
    const desired = new THREE.Vector3(
      -state.vx * 8 + 6,
      Math.max(2, state.alt + 4),
      -state.vy * 8 + 6,
    );
    camera.position.lerp(desired, Math.min(1, dt * 1.5));
    camera.lookAt(0, state.alt + 0.4, 0);
  });
  return null;
}