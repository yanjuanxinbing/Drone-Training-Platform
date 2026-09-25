"use client";

export function Mountain({ accent }: { accent: string }) {
  const peaks = Array.from({ length: 7 }).map((_, i) => {
    const a = (i / 7) * Math.PI * 2;
    const r = 12 + (i % 3) * 4;
    const x = Math.cos(a) * r;
    const z = Math.sin(a) * r;
    const h = 6 + (i * 2.1) % 14;
    return { x, z, h };
  });
  return (
    <group>
      {/* Sky-toned ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
        <planeGeometry args={[100, 100]} />
        <meshStandardMaterial color="#2A2A28" />
      </mesh>
      {/* Snow line plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 4, 0]} receiveShadow>
        <planeGeometry args={[100, 100]} />
        <meshStandardMaterial color="#E8E8E5" transparent opacity={0.18} />
      </mesh>
      {/* Peaks */}
      {peaks.map((p, i) => (
        <group key={i} position={[p.x, 0, p.z]}>
          <mesh position={[0, p.h / 2, 0]} castShadow>
            <coneGeometry args={[5, p.h, 6]} />
            <meshStandardMaterial color="#3A3A37" flatShading />
          </mesh>
          {/* Snow cap */}
          <mesh position={[0, p.h - 0.6, 0]} castShadow>
            <coneGeometry args={[2.2, 1.2, 6]} />
            <meshStandardMaterial color="#E8E8E5" flatShading />
          </mesh>
        </group>
      ))}
      {/* RTH beacon */}
      <mesh position={[0, 0.3, 0]}>
        <cylinderGeometry args={[0.6, 0.6, 0.6, 16]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.7} />
      </mesh>
      <mesh position={[0, 1.2, 0]}>
        <coneGeometry args={[0.18, 0.6, 8]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
      </mesh>
    </group>
  );
}