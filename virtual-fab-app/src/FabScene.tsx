import { ContactShadows, Html, OrbitControls } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Mesh } from 'three'
import type { Scenario } from './types'

const STATION_LAYOUT: Record<string, [number, number, number]> = {
  alert: [-5, 0, -1.8],
  coach: [-3, 0, 2],
  data: [0, 0, 2.5],
  doe: [3.2, 0, 1.8],
  analysis: [5, 0, -1.2],
  validation: [1.4, 0, -3],
}

function Station({
  position,
  label,
  index,
  active,
  complete,
  onSelect,
}: {
  position: [number, number, number]
  label: string
  index: number
  active: boolean
  complete: boolean
  onSelect: () => void
}) {
  const marker = useRef<Mesh>(null)
  useFrame(({ clock }) => {
    if (marker.current && active) {
      marker.current.position.y = 2.25 + Math.sin(clock.elapsedTime * 2.4) * 0.12
      marker.current.rotation.y = clock.elapsedTime * 0.7
    }
  })
  const color = active ? '#00a8b5' : complete ? '#178b70' : '#65747a'

  return (
    <group position={position}>
      <mesh
        position={[0, 0.45, 0]}
        onClick={(event) => {
          event.stopPropagation()
          onSelect()
        }}
        onPointerOver={() => { document.body.style.cursor = 'pointer' }}
        onPointerOut={() => { document.body.style.cursor = 'default' }}
      >
        <boxGeometry args={[1.65, 0.9, 1.3]} />
        <meshStandardMaterial color={color} roughness={0.58} metalness={0.15} />
      </mesh>
      <mesh position={[0, 1.08, 0]}>
        <boxGeometry args={[1.2, 0.14, 0.88]} />
        <meshStandardMaterial color={active ? '#dffcff' : '#c9d4d6'} />
      </mesh>
      <Html position={[0, 1.48, 0]} center distanceFactor={11}>
        <div className={`station-tag ${active ? 'active' : complete ? 'complete' : ''}`}>
          <span>{String(index + 1).padStart(2, '0')}</span>{label}
        </div>
      </Html>
      {active && (
        <mesh ref={marker} position={[0, 2.25, 0]} rotation={[Math.PI / 4, 0, Math.PI / 4]}>
          <octahedronGeometry args={[0.22, 0]} />
          <meshStandardMaterial color="#ffb21d" emissive="#7a4300" emissiveIntensity={0.8} />
        </mesh>
      )}
      <mesh position={[0, 0.04, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.9, 1.05, 32]} />
        <meshBasicMaterial color={active ? '#ffb21d' : complete ? '#5dd6b7' : '#9da9ab'} />
      </mesh>
    </group>
  )
}

function Wafer() {
  const wafer = useRef<Mesh>(null)
  useFrame((_, delta) => {
    if (wafer.current) wafer.current.rotation.z += delta * 0.18
  })
  return (
    <mesh ref={wafer} position={[0, 0.14, -0.2]} rotation={[Math.PI / 2, 0, 0]}>
      <cylinderGeometry args={[1.05, 1.05, 0.08, 64]} />
      <meshStandardMaterial color="#9fe4e7" metalness={0.55} roughness={0.25} />
    </mesh>
  )
}

export function FabScene({ scenario, stageIndex, onStationSelect }: { scenario: Scenario; stageIndex: number; onStationSelect: (index: number) => void }) {
  const pathPoints = useMemo(() => scenario.stages.map((stage) => STATION_LAYOUT[stage.station]), [scenario])
  return (
    <div className="scene-wrap" aria-label="가상 팹 공정 스테이션">
      <Canvas camera={{ position: [10, 9, 11], fov: 38 }} dpr={[1, 1.65]}>
        <color attach="background" args={['#e8eff0']} />
        <ambientLight intensity={1.7} />
        <directionalLight position={[5, 10, 6]} intensity={2.2} castShadow />
        <gridHelper args={[18, 18, '#b5c5c8', '#d3dfe1']} position={[0, 0, 0]} />
        <mesh position={[0, -0.04, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[18, 14]} />
          <meshStandardMaterial color="#eef3f4" roughness={0.9} />
        </mesh>
        <Wafer />
        {pathPoints.map((point, index) => index < pathPoints.length - 1 && (
          <mesh key={`path-${index}`} position={[(point[0] + pathPoints[index + 1][0]) / 2, 0.015, (point[2] + pathPoints[index + 1][2]) / 2]} rotation={[-Math.PI / 2, 0, Math.atan2(pathPoints[index + 1][2] - point[2], pathPoints[index + 1][0] - point[0])] }>
            <planeGeometry args={[Math.hypot(pathPoints[index + 1][0] - point[0], pathPoints[index + 1][2] - point[2]), 0.08]} />
            <meshBasicMaterial color={index < stageIndex ? '#178b70' : '#9fb0b3'} />
          </mesh>
        ))}
        {scenario.stages.map((stage, index) => (
          <Station
            key={stage.id}
            position={STATION_LAYOUT[stage.station]}
            label={stage.label}
            index={index}
            active={index === stageIndex}
            complete={index < stageIndex}
            onSelect={() => onStationSelect(index)}
          />
        ))}
        <ContactShadows position={[0, 0.01, 0]} opacity={0.18} scale={16} blur={2.8} far={8} />
        <OrbitControls enablePan={false} minDistance={9} maxDistance={18} minPolarAngle={0.72} maxPolarAngle={1.2} target={[0, 0.5, 0]} />
      </Canvas>
      <div className="scene-help">드래그해 회전 · 휠로 확대 · 현재 스테이션 클릭</div>
    </div>
  )
}
