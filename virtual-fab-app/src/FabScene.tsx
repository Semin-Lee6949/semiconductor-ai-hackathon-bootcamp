import { ContactShadows, Html, OrbitControls } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Group, Mesh } from 'three'
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

const EXHIBIT_LABELS = ['EDGE CD WAFER', 'OLLAMA EVIDENCE MENTOR', 'WAFER MAP', 'SCREENING DOE', 'ANALYSIS TOOL BAY', 'HOLDOUT GATE']

function WaferDisc({ position = [0, 1.35, 0] as [number, number, number], color = '#9fe4e7', defects = false }: { position?: [number, number, number]; color?: string; defects?: boolean }) {
  return <group position={position} rotation={[Math.PI / 2, 0, 0]}>
    <mesh><cylinderGeometry args={[1.08, 1.08, 0.09, 64]} /><meshStandardMaterial color={color} metalness={0.45} roughness={0.28} /></mesh>
    <mesh position={[0, .055, 0]}><ringGeometry args={[.98, 1.06, 64]} /><meshBasicMaterial color={defects ? '#ff9d00' : '#2a9e93'} /></mesh>
    {defects && [[.75,.55],[-.72,.58],[.88,-.35],[-.8,-.42],[.25,-.94]].map(([x, z], index) => <mesh key={index} position={[x,.09,z]}><sphereGeometry args={[.09,16,16]}/><meshStandardMaterial color="#ff9d00" emissive="#7b3900" emissiveIntensity={.7}/></mesh>)}
  </group>
}

function MentorConsole() {
  const nodes = [[-1.2,1.7,-.2],[-.65,2.35,.1],[.25,2.55,0],[1.05,2.05,.15],[1.25,1.25,-.1]] as [number,number,number][]
  return <group>
    <mesh position={[0,.45,0]}><boxGeometry args={[2.6,.75,1.4]}/><meshStandardMaterial color="#173d46" metalness={.2}/></mesh>
    <mesh position={[0,1.25,.28]} rotation={[-.18,0,0]}><boxGeometry args={[2.15,1.15,.1]}/><meshStandardMaterial color="#00a8b5" emissive="#004f57" emissiveIntensity={.55}/></mesh>
    {nodes.map((position,index)=><mesh key={index} position={position}><sphereGeometry args={[.13,16,16]}/><meshStandardMaterial color={index===2?'#ffb21d':'#dffcff'} emissive="#006e76" emissiveIntensity={.5}/></mesh>)}
    <Html position={[0,1.28,.38]} center distanceFactor={9}><div className="console-copy"><b>OLLAMA</b><span>가설 → 반증 → 증거</span></div></Html>
  </group>
}

function WaferMap() {
  const cells = Array.from({ length: 49 }, (_, index) => ({ x: index % 7 - 3, z: Math.floor(index / 7) - 3 }))
  return <group position={[0,.12,0]}>{cells.map(({x,z}) => {
    const radius = Math.hypot(x,z); if (radius > 3.45) return null
    const risk = radius > 2.45 && (x + z) % 2 === 0
    return <mesh key={`${x}-${z}`} position={[x*.32, risk ? .22 : .12, z*.32]}><boxGeometry args={[.27, risk ? .42 : .2,.27]}/><meshStandardMaterial color={risk?'#e58a00':'#59b9bf'} /></mesh>
  })}<mesh position={[0,.015,0]} rotation={[-Math.PI/2,0,0]}><ringGeometry args={[1.12,1.18,48]}/><meshBasicMaterial color="#071d24"/></mesh></group>
}

function DoeMatrix() {
  const values = [.35,.72,.48,.82,1.18,.65,.42,.9,.55]
  return <group position={[0,0,0]}>{values.map((height,index)=>{
    const x=index%3-1, z=Math.floor(index/3)-1
    return <group key={index} position={[x*.65,0,z*.65]}><mesh position={[0,height/2,0]}><boxGeometry args={[.46,height,.46]}/><meshStandardMaterial color={index===4?'#ffb21d':'#2ba7af'}/></mesh><Html position={[0,height+.18,0]} center distanceFactor={9}><span className="doe-value">{index+1}</span></Html></group>
  })}</group>
}

function AnalysisTools() {
  return <group>
    <group position={[-1.15,0,0]}><mesh position={[0,.65,0]}><boxGeometry args={[.85,1.3,.9]}/><meshStandardMaterial color="#31535b"/></mesh><mesh position={[0,1.55,0]}><cylinderGeometry args={[.28,.4,.65,24]}/><meshStandardMaterial color="#dbe6e7"/></mesh><Html position={[0,2,0]} center distanceFactor={9}><span className="tool-tag">SEM</span></Html></group>
    <group position={[0,0,.1]}><mesh position={[0,.32,0]}><cylinderGeometry args={[.72,.72,.18,48]}/><meshStandardMaterial color="#9fe4e7" metalness={.5}/></mesh><mesh position={[0,1.05,0]}><cylinderGeometry args={[.12,.22,1.1,24]}/><meshStandardMaterial color="#ffb21d"/></mesh><Html position={[0,1.8,0]} center distanceFactor={9}><span className="tool-tag">OPTICAL CD</span></Html></group>
    <group position={[1.2,0,0]}><mesh position={[0,.6,0]}><boxGeometry args={[.9,1.2,.9]}/><meshStandardMaterial color="#31535b"/></mesh><mesh position={[0,1.34,.32]} rotation={[Math.PI/2,0,0]}><torusGeometry args={[.27,.07,12,32]}/><meshStandardMaterial color="#ffb21d"/></mesh><Html position={[0,1.9,0]} center distanceFactor={9}><span className="tool-tag">I–V</span></Html></group>
  </group>
}

function ValidationGate() {
  return <group><WaferDisc position={[-1.15,1.05,0]} color="#b9c6c8" defects/><WaferDisc position={[1.15,1.05,0]} color="#82d8c3"/><mesh position={[0,1.1,0]} rotation={[0,0,-Math.PI/2]}><coneGeometry args={[.22,.65,20]}/><meshStandardMaterial color="#ffb21d"/></mesh><Html position={[-1.15,2.45,0]} center distanceFactor={10}><span className="tool-tag muted">BASELINE</span></Html><Html position={[1.15,2.45,0]} center distanceFactor={10}><span className="tool-tag">HOLDOUT</span></Html></group>
}

function StageExhibit({ stageIndex }: { stageIndex: number }) {
  const exhibit = useRef<Group>(null)
  useFrame(({ clock }) => { if (exhibit.current) exhibit.current.position.y = .15 + Math.sin(clock.elapsedTime * 1.4) * .045 })
  return <group ref={exhibit} position={[0,.15,-.15]}>
    {stageIndex === 0 && <WaferDisc defects/>}
    {stageIndex === 1 && <MentorConsole/>}
    {stageIndex === 2 && <WaferMap/>}
    {stageIndex === 3 && <DoeMatrix/>}
    {stageIndex === 4 && <AnalysisTools/>}
    {stageIndex === 5 && <ValidationGate/>}
  </group>
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
        <StageExhibit key={stageIndex} stageIndex={stageIndex} />
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
      <div className="exhibit-label"><span>ACTIVE MODEL</span><b>{EXHIBIT_LABELS[stageIndex]}</b></div>
      <div className="scene-help">드래그해 회전 · 휠로 확대 · 현재 스테이션 클릭</div>
    </div>
  )
}
