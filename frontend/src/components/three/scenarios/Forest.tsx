"use client";

export function Forest({ accent }: { accent: string }) {
  const trees = Array.from({ length: 36 }).map((_, i) => {
    const angle = (i * 1.3) + (i % 5) * 0.5;
    const r = 4 + ((i * 7) % 18);
    const x = Math.cos(angle) * r + ((i % 3) - 1) * 2;
    const z = Math.sin(angle) * r + ((i % 4) - 2) * 1.5;
    const h = 3 + ((i * 1.3) % 4);
    return { x, z, h };
  });
  return (
    <group>
      {/* Ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[80, 80]} />
        <meshStandardMaterial color="#1F1F1D" />
      </mesh>
      {/* Path */}
      <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[1.6, 80]} />
        <meshStandardMaterial color="#8B6F4E" />
      </mesh>
      {/* Trees — cones */}
      {trees.map((t, i) => (
        <group key={i} position={[t.x, 0, t.z]}>
          <mesh position={[0, t.h / 2, 0]} castShadow>
            <coneGeometry args={[1.4, t.h, 12]} />
            <meshStandardMaterial color="#2A2A28" />
          </mesh>
          <mesh position={[0, 0.2, 0]} castShadow>
            <cylinderGeometry args={[0.16, 0.18, 0.4]} />
            <meshStandardMaterial color="#3A3A37" />
          </mesh>
        </group>
      ))}
      {/* Target marker */}
      <mesh position={[8, 0.05, 4]}>
        <ringGeometry args={[0.6, 0.9, 24]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.6} />
      </mesh>
    </group>
  );
}