"use client";

export function Urban({ accent }: { accent: string }) {
  const towers = Array.from({ length: 14 }).map((_, i) => {
    const a = (i / 14) * Math.PI * 2;
    const r = 14 + (i % 3) * 3;
    const x = Math.cos(a) * r;
    const z = Math.sin(a) * r;
    const w = 3 + (i % 4) * 1.2;
    const h = 8 + (i * 1.7) % 18;
    return { x, z, w, h };
  });
  return (
    <group>
      {/* Ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[60, 60]} />
        <meshStandardMaterial color="#2A2A28" />
      </mesh>
      {/* Road grid */}
      {Array.from({ length: 8 }).map((_, i) => (
        <mesh key={`r-${i}`} position={[-30 + i * 8, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[0.4, 60]} />
          <meshStandardMaterial color="#4A4A47" />
        </mesh>
      ))}
      {Array.from({ length: 8 }).map((_, i) => (
        <mesh key={`c-${i}`} position={[0, 0.01, -30 + i * 8]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[60, 0.4]} />
          <meshStandardMaterial color="#4A4A47" />
        </mesh>
      ))}
      {/* Towers */}
      {towers.map((t, i) => (
        <mesh key={i} position={[t.x, t.h / 2, t.z]} castShadow receiveShadow>
          <boxGeometry args={[t.w, t.h, t.w]} />
          <meshStandardMaterial color="#3A3A37" />
        </mesh>
      ))}
      {/* Accent: a single lit window panel on each tower */}
      {towers.map((t, i) => (
        <mesh key={`lit-${i}`} position={[t.x + t.w / 2 + 0.01, t.h * 0.7, t.z]}>
          <planeGeometry args={[t.w * 0.4, t.h * 0.1]} />
          <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.4} />
        </mesh>
      ))}
      {/* Central inspection target */}
      <mesh position={[0, 1.5, 0]} castShadow>
        <torusGeometry args={[1, 0.08, 16, 32]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
      </mesh>
    </group>
  );
}