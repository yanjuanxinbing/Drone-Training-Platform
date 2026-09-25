"use client";

export function Indoor({ accent }: { accent: string }) {
  const cols = Array.from({ length: 4 }).map((_, i) => {
    const x = (i - 1.5) * 4;
    return { x, h: 7 };
  });
  return (
    <group>
      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[40, 40]} />
        <meshStandardMaterial color="#F4F4F1" />
      </mesh>
      {/* Walls */}
      <mesh position={[0, 4, -15]} receiveShadow>
        <planeGeometry args={[40, 8]} />
        <meshStandardMaterial color="#FFFFFF" side={2} />
      </mesh>
      <mesh position={[0, 4, 15]} rotation={[0, Math.PI, 0]} receiveShadow>
        <planeGeometry args={[40, 8]} />
        <meshStandardMaterial color="#FFFFFF" side={2} />
      </mesh>
      <mesh position={[-15, 4, 0]} rotation={[0, Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[40, 8]} />
        <meshStandardMaterial color="#F4F4F1" side={2} />
      </mesh>
      <mesh position={[15, 4, 0]} rotation={[0, -Math.PI / 2, 0]} receiveShadow>
        <planeGeometry args={[40, 8]} />
        <meshStandardMaterial color="#F4F4F1" side={2} />
      </mesh>
      {/* Ceiling */}
      <mesh position={[0, 8, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <planeGeometry args={[40, 40]} />
        <meshStandardMaterial color="#FFFFFF" side={2} />
      </mesh>
      {/* Columns to inspect */}
      {cols.map((c, i) => (
        <mesh key={i} position={[c.x, c.h / 2, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[0.35, 0.35, c.h, 16]} />
          <meshStandardMaterial color="#E8E8E5" />
        </mesh>
      ))}
      {/* Landing pad */}
      <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <ringGeometry args={[0.28, 0.32, 32]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.7} />
      </mesh>
      <mesh position={[0, 0.025, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.3, 32]} />
        <meshStandardMaterial color="#1A1A18" />
      </mesh>
    </group>
  );
}