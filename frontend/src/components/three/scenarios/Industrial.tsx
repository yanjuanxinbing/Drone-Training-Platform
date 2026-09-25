"use client";

export function Industrial({ accent }: { accent: string }) {
  const turbines = Array.from({ length: 5 }).map((_, i) => ({
    x: (i - 2) * 5,
    z: -8,
  }));
  return (
    <group>
      {/* Ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[80, 80]} />
        <meshStandardMaterial color="#1A1A18" />
      </mesh>
      {/* Substation pad */}
      <mesh position={[0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial color="#3A3A37" />
      </mesh>
      {/* Power pylons */}
      {turbines.map((t, i) => (
        <group key={i} position={[t.x, 0, t.z]}>
          {/* Mast */}
          <mesh position={[0, 4, 0]} castShadow>
            <cylinderGeometry args={[0.08, 0.16, 8, 12]} />
            <meshStandardMaterial color="#E8E8E5" />
          </mesh>
          {/* Cross arms */}
          <mesh position={[0, 6, 0]} castShadow>
            <boxGeometry args={[3.2, 0.16, 0.16]} />
            <meshStandardMaterial color="#E8E8E5" />
          </mesh>
          <mesh position={[0, 4.6, 0]} castShadow>
            <boxGeometry args={[2.6, 0.16, 0.16]} />
            <meshStandardMaterial color="#E8E8E5" />
          </mesh>
          {/* Conductors */}
          {[-1.6, 0, 1.6].map((dx, idx) => (
            <mesh key={idx} position={[dx, 6, 0]}>
              <sphereGeometry args={[0.06, 8, 8]} />
              <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
            </mesh>
          ))}
        </group>
      ))}
      {/* Pipeline */}
      {Array.from({ length: 20 }).map((_, i) => (
        <mesh key={i} position={[-12 + i * 1.2, 0.5, 8]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.18, 0.18, 1.2, 12]} />
          <meshStandardMaterial color="#6B6B68" />
        </mesh>
      ))}
      {/* Thermal anomaly markers */}
      {[
        [2, 0.1, 8],
        [-4, 0.1, 8],
        [7, 0.1, 8],
        [-7, 0.1, 8],
        [4, 0.1, 8],
      ].map((p, i) => (
        <mesh key={i} position={p as [number, number, number]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.4, 0.6, 24]} />
          <meshStandardMaterial color="#D94F1E" emissive="#D94F1E" emissiveIntensity={0.5} />
        </mesh>
      ))}
      {/* Inspection target */}
      <mesh position={[0, 2, 0]}>
        <torusGeometry args={[1.2, 0.08, 16, 32]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.5} />
      </mesh>
    </group>
  );
}