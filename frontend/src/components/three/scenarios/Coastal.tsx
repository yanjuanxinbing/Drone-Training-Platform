"use client";

export function Coastal({ accent }: { accent: string }) {
  const buoys = [
    { x: -6, z: 4 },
    { x: 7, z: -3 },
  ];
  return (
    <group>
      {/* Sea */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
        <planeGeometry args={[100, 100]} />
        <meshStandardMaterial color="#1F3A4A" />
      </mesh>
      {/* Sand bar */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[14, 0, 0]} receiveShadow>
        <planeGeometry args={[14, 100]} />
        <meshStandardMaterial color="#8B6F4E" />
      </mesh>
      {/* Wave strokes */}
      {Array.from({ length: 12 }).map((_, i) => (
        <mesh key={i} position={[i * 1.4 - 7, 0.02, -8 + i * 0.8]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.3, 0.55, 16]} />
          <meshStandardMaterial color="#FFFFFF" transparent opacity={0.18} />
        </mesh>
      ))}
      {/* NFZ cylinders */}
      {[[-10, -2, 8], [10, 6, 8], [-3, 10, 7]].map((p, i) => (
        <group key={i} position={p as [number, number, number]}>
          <mesh>
            <cylinderGeometry args={[p[2], p[2], 0.05, 32, 1, true]} />
            <meshStandardMaterial color="#D94F1E" transparent opacity={0.18} side={2} />
          </mesh>
        </group>
      ))}
      {/* Buoys */}
      {buoys.map((b, i) => (
        <group key={i} position={[b.x, 0.4, b.z]}>
          <mesh castShadow>
            <cylinderGeometry args={[0.32, 0.4, 0.6, 16]} />
            <meshStandardMaterial color="#C9A47A" />
          </mesh>
          <mesh position={[0, 0.6, 0]} castShadow>
            <sphereGeometry args={[0.18, 16, 16]} />
            <meshStandardMaterial color="#D94F1E" />
          </mesh>
          <mesh position={[0, 1.0, 0]}>
            <coneGeometry args={[0.04, 0.6, 6]} />
            <meshStandardMaterial color="#1A1A18" />
          </mesh>
          {/* Marker */}
          <mesh position={[0, 0.04, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.5, 0.7, 24]} />
            <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.5} />
          </mesh>
        </group>
      ))}
    </group>
  );
}