import { ContactShadows, Html } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Vector3 } from 'three'
import type { Group, Mesh } from 'three'
import type { ScenarioSummary } from './types'

const ENTRY_STEPS = [
  { code: 'ACCESS', title: '가상 팹 접속', copy: '오늘의 임무는 공정 순서를 외우는 것이 아니다. 평균값 뒤에 숨은 이상 신호를 데이터로 추적하고, 제한된 시간과 예산 안에서 원인을 좁혀야 한다.', action: '출입 등록 시작' },
  { code: 'WASH', title: '손 씻기', copy: '손과 손목의 오염원을 제거한다. 실제 클린룸 절차를 단순화한 교육 장면이며, 이 게임의 본체는 입실 뒤 시작되는 불량 원인 진단이다.', action: '세정 완료' },
  { code: 'MASK', title: '마스크 착용', copy: '비말과 호흡 입자의 유입을 줄인다. 마스크가 얼굴을 완전히 덮었는지 확인한 뒤 다음 준비실로 이동한다.', action: '마스크 착용' },
  { code: 'GOWN', title: '방진복 착용', copy: '머리카락과 의복에서 발생하는 입자를 격리한다. 장갑·후드·방진복이 준비되면 오염 구역과 청정 구역의 경계를 통과할 수 있다.', action: '방진복 착용' },
  { code: 'AIR SHOWER', title: '에어샤워 통과', copy: '고속 청정 공기가 방진복 표면의 잔류 입자를 제거한다. 문이 열리면 여섯 공정룸 중 하나를 골라 실제 사건 해결을 시작한다.', action: '에어샤워 가동' },
] as const

const ENTRY_POSITIONS: Array<[number, number, number]> = [
  [-5.6, 0, 1.3], [-3.4, 0, .6], [-1.2, 0, .2], [1.15, 0, .2], [3.55, 0, .1], [0, 0, -2.7],
]

function CameraRig({ step, reducedMotion }: { step: number; reducedMotion: boolean }) {
  const { camera } = useThree()
  const targetPosition = useMemo(() => step === 5 ? new Vector3(0, 5.3, 10.8) : new Vector3(6.8, 4.2, 8.5), [step])
  const targetLook = useMemo(() => step === 5 ? new Vector3(0, 1.1, -2.2) : new Vector3(ENTRY_POSITIONS[step][0], 1, ENTRY_POSITIONS[step][2]), [step])

  useEffect(() => {
    if (!reducedMotion) return
    camera.position.copy(targetPosition)
    camera.lookAt(targetLook)
    camera.updateProjectionMatrix()
  }, [camera, reducedMotion, targetLook, targetPosition])

  useFrame(() => {
    if (reducedMotion) return
    camera.position.lerp(targetPosition, .045)
    camera.lookAt(targetLook)
  })
  return null
}

function FacilityShell({ hall }: { hall: boolean }) {
  return <group>
    <mesh position={[0, -.06, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[18, 13]}/><meshStandardMaterial color={hall ? '#0e3038' : '#d9e9e9'} metalness={.18} roughness={.62}/></mesh>
    <gridHelper args={[18, 18, hall ? '#1e6d77' : '#9fbabc', hall ? '#184852' : '#c5d7d8']} position={[0, 0, 0]}/>
    <mesh position={[0, 2.75, -4.2]}><boxGeometry args={[18, 5.5, .22]}/><meshStandardMaterial color={hall ? '#08242c' : '#edf6f5'} metalness={.2}/></mesh>
    <mesh position={[-8.8, 2.5, 0]}><boxGeometry args={[.18, 5, 8.5]}/><meshStandardMaterial color="#c7d8d9" transparent opacity={hall ? .18 : .7}/></mesh>
    <mesh position={[8.8, 2.5, 0]}><boxGeometry args={[.18, 5, 8.5]}/><meshStandardMaterial color="#c7d8d9" transparent opacity={hall ? .18 : .7}/></mesh>
    {[-6,-3,0,3,6].map((x) => <group key={x}><mesh position={[x,5.05,0]}><boxGeometry args={[.08,.12,8]}/><meshBasicMaterial color={hall ? '#38e1eb' : '#7bcbd0'}/></mesh><pointLight position={[x,4.6,0]} color={hall ? '#51f4ff' : '#c8ffff'} intensity={hall ? 6 : 2.5} distance={6}/></group>)}
    <fog attach="fog" args={[hall ? '#071c23' : '#dbe8e8', 11, 25]}/>
  </group>
}

function SinkStation({ active }: { active: boolean }) {
  const water = useRef<Mesh>(null)
  useFrame(({ clock }) => { if (water.current && active) water.current.scale.y = .8 + Math.sin(clock.elapsedTime * 10) * .14 })
  return <group position={[-3.4,0,.6]}>
    <mesh position={[0,.74,0]}><boxGeometry args={[1.5,.25,1]}/><meshStandardMaterial color="#dbe7e7" metalness={.65} roughness={.18}/></mesh>
    <mesh position={[0,.84,0]}><cylinderGeometry args={[.55,.42,.18,30]}/><meshStandardMaterial color="#88aeb3" metalness={.8}/></mesh>
    <mesh position={[0,1.28,-.35]}><torusGeometry args={[.32,.07,12,28,Math.PI]}/><meshStandardMaterial color="#54777d" metalness={.8}/></mesh>
    <mesh ref={water} visible={active} position={[0,1.02,-.08]}><cylinderGeometry args={[.025,.04,.55,10]}/><meshStandardMaterial color="#5de9ff" emissive="#008da3" emissiveIntensity={1.2} transparent opacity={.7}/></mesh>
    <Html position={[0,1.75,0]} center><span className={`lobby-station-tag ${active ? 'active' : ''}`}>01 · HAND WASH</span></Html>
  </group>
}

function MaskStation({ active }: { active: boolean }) {
  return <group position={[-1.2,0,.2]}>
    <mesh position={[0,1.05,0]}><boxGeometry args={[1.2,2.1,.75]}/><meshStandardMaterial color={active ? '#1d8793' : '#567078'} metalness={.24}/></mesh>
    <mesh position={[0,1.42,.4]}><boxGeometry args={[.68,.42,.08]}/><meshStandardMaterial color="#7df2f2" emissive="#007e88" emissiveIntensity={.8}/></mesh>
    <mesh position={[0,.73,.48]} rotation={[0,0,.08]}><boxGeometry args={[.72,.38,.05]}/><meshStandardMaterial color="#d9ffff"/></mesh>
    <Html position={[0,2.45,0]} center><span className={`lobby-station-tag ${active ? 'active' : ''}`}>02 · MASK</span></Html>
  </group>
}

function GownStation({ active }: { active: boolean }) {
  return <group position={[1.15,0,.2]}>
    <mesh position={[0,1.55,-.2]}><boxGeometry args={[1.8,.12,.75]}/><meshStandardMaterial color="#41636a" metalness={.5}/></mesh>
    {[-.55,0,.55].map((x,index) => <group key={x} position={[x,1.1,0]}><mesh><cylinderGeometry args={[.25,.42,1.45,12]}/><meshStandardMaterial color={active && index===1 ? '#f7ffff' : '#bdd1d3'}/></mesh><mesh position={[0,.82,0]}><sphereGeometry args={[.26,14,10]}/><meshStandardMaterial color="#e9f4f3"/></mesh></group>)}
    <Html position={[0,2.45,0]} center><span className={`lobby-station-tag ${active ? 'active' : ''}`}>03 · GOWNING</span></Html>
  </group>
}

function AirShower({ active, open }: { active: boolean; open: boolean }) {
  const particles = useRef<Group>(null)
  useFrame(({ clock }) => { if (particles.current && active) particles.current.rotation.y = clock.elapsedTime * 2.4 })
  return <group position={[3.55,0,.1]}>
    <mesh position={[0,1.65,-.15]}><boxGeometry args={[2.25,3.3,1.8]}/><meshStandardMaterial color="#68858b" metalness={.72} roughness={.23} transparent opacity={.42}/></mesh>
    <mesh position={[-.98,1.65,.78]} rotation={[0,open ? -1.2 : 0,0]}><boxGeometry args={[.12,3.1,1.62]}/><meshStandardMaterial color="#a8f3f1" transparent opacity={.46}/></mesh>
    <mesh position={[.98,1.65,.78]} rotation={[0,open ? 1.2 : 0,0]}><boxGeometry args={[.12,3.1,1.62]}/><meshStandardMaterial color="#a8f3f1" transparent opacity={.46}/></mesh>
    <group ref={particles}>{Array.from({length:24},(_,i) => { const a=(i/24)*Math.PI*2; return <mesh key={i} visible={active} position={[Math.cos(a)*.65,.4+(i%6)*.45,Math.sin(a)*.5]}><sphereGeometry args={[.025,6,6]}/><meshBasicMaterial color="#aaffff"/></mesh> })}</group>
    <Html position={[0,3.75,0]} center><span className={`lobby-station-tag ${active ? 'active' : ''}`}>04 · AIR SHOWER</span></Html>
  </group>
}

function Rookie({ step }: { step: number }) {
  const root = useRef<Group>(null)
  const target = useMemo(() => new Vector3(...ENTRY_POSITIONS[step]), [step])
  useFrame(() => { if (root.current) root.current.position.lerp(target, .055) })
  const masked = step >= 2
  const gowned = step >= 3
  return <group ref={root} position={ENTRY_POSITIONS[0]} scale={.72}>
    <mesh position={[0,.42,0]}><boxGeometry args={[.34,.82,.36]}/><meshStandardMaterial color={gowned ? '#f4fbfb' : '#213f48'}/></mesh>
    <mesh position={[0,1.18,0]}><cylinderGeometry args={[.42,.48,.9,12]}/><meshStandardMaterial color={gowned ? '#f4fbfb' : '#26a8b2'}/></mesh>
    <mesh position={[0,1.93,0]}><sphereGeometry args={[.43,18,14]}/><meshStandardMaterial color={gowned ? '#eaf5f4' : '#e6b991'}/></mesh>
    {gowned && <mesh position={[0,2.02,-.04]}><sphereGeometry args={[.52,18,14]}/><meshStandardMaterial color="#f7ffff" side={1}/></mesh>}
    {masked && <mesh position={[0,1.86,.38]} scale={[1,.55,.18]}><sphereGeometry args={[.34,14,10]}/><meshStandardMaterial color="#a8eff1"/></mesh>}
    <mesh position={[-.48,1.18,0]} rotation={[0,0,-.12]}><boxGeometry args={[.22,.9,.24]}/><meshStandardMaterial color={gowned ? '#f4fbfb' : '#26a8b2'}/></mesh>
    <mesh position={[.48,1.18,0]} rotation={[0,0,.12]}><boxGeometry args={[.22,.9,.24]}/><meshStandardMaterial color={gowned ? '#f4fbfb' : '#26a8b2'}/></mesh>
  </group>
}

function RoomDoor({ item, index, onSelect }: { item: ScenarioSummary; index: number; onSelect: () => void }) {
  const x = -6.25 + index * 2.5
  return <group position={[x,0,-4.02]}>
    <mesh position={[0,1.48,.16]} onClick={onSelect} onPointerOver={() => { document.body.style.cursor='pointer' }} onPointerOut={() => { document.body.style.cursor='default' }}>
      <boxGeometry args={[1.82,2.95,.18]}/><meshStandardMaterial color={index === 0 ? '#0ea4b0' : '#174751'} emissive={index === 0 ? '#006674' : '#07191d'} emissiveIntensity={.55} metalness={.55}/>
    </mesh>
    <mesh position={[0,2.55,.3]}><boxGeometry args={[1.34,.3,.06]}/><meshBasicMaterial color={index === 0 ? '#ffe085' : '#69e9ef'}/></mesh>
    <Html position={[0,1.5,.4]} center distanceFactor={10}><button className="room-door-label" onClick={onSelect}><span>{item.module_no}</span><b>{item.process}</b><small>{item.title}</small></button></Html>
  </group>
}

function LobbyScene({ step, scenarios, onSelect, reducedMotion }: { step: number; scenarios: ScenarioSummary[]; onSelect: (id: string) => void; reducedMotion: boolean }) {
  const hall = step === 5
  return <Canvas camera={{position:[6.8,4.2,8.5],fov:42}} dpr={[1,1.5]} frameloop={reducedMotion ? 'demand' : 'always'}>
    <color attach="background" args={[hall ? '#071c23' : '#dbe8e8']}/>
    <ambientLight intensity={hall ? 1.1 : 2.1}/><directionalLight position={[5,9,6]} intensity={hall ? 2.2 : 3.2}/>
    <FacilityShell hall={hall}/><CameraRig step={step} reducedMotion={reducedMotion}/>
    {!hall && <><SinkStation active={step===1}/><MaskStation active={step===2}/><GownStation active={step===3}/><AirShower active={step===4} open={step>=4}/><Rookie step={step}/></>}
    {hall && scenarios.map((item,index)=><RoomDoor key={item.id} item={item} index={index} onSelect={() => onSelect(item.id)}/>)}
    <ContactShadows position={[0,.01,0]} opacity={hall ? .32 : .18} scale={18} blur={2.8} far={8}/>
  </Canvas>
}

export function CleanroomLobby({ scenarios, loading, error, onSelect }: { scenarios: ScenarioSummary[]; loading: boolean; error: string; onSelect: (id: string) => void }) {
  const [step,setStep] = useState(0)
  const [focusedId,setFocusedId] = useState('photo-cd-drift')
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const focused = scenarios.find((item)=>item.id===focusedId) ?? scenarios[0]
  const hall = step===5
  const advance = () => setStep((current)=>Math.min(5,current+1))

  return <main className={`cleanroom-lobby ${hall?'hall-open':''}`}>
    <header className="game-topbar"><div><b>VIRTUAL FAB</b><span>FACILITY 01 · SCHOLARBRIDGE</span></div><div><span>ACCESS</span><strong>{hall?'GRANTED':`${step}/4`}</strong></div></header>
    <section className="lobby-viewport" aria-label="가상 클린룸 입실 화면">
      <LobbyScene step={step} scenarios={scenarios} onSelect={onSelect} reducedMotion={reducedMotion}/>
      <div className="scanlines" aria-hidden="true"/>
      <div className="entry-progress" aria-label="클린룸 입실 진행 단계">{ENTRY_STEPS.map((item,index)=><div key={item.code} className={index<step?'done':index===step?'active':''}><span>{String(index+1).padStart(2,'0')}</span><b>{item.code}</b></div>)}</div>
      {!hall && <section className="guide-dialog" aria-live="polite"><div className="guide-portrait"><span>AI</span><b>SAFETY<br/>GUIDE</b></div><div><span>ENTRY PROTOCOL {String(step+1).padStart(2,'0')}</span><h1>{ENTRY_STEPS[step].title}</h1><p>{ENTRY_STEPS[step].copy}</p><button type="button" onClick={advance}>{ENTRY_STEPS[step].action}<b>→</b></button></div></section>}
      {hall && <section className="mission-console"><header><div><span>CLEANROOM ACCESS GRANTED</span><h1>사건이 기다리는 공정룸을 선택해.</h1></div><p>문을 열면 60–90분의 제한시간이 시작돼.<br/>정답이 아니라 증거의 순서를 보여줘.</p></header>
        {loading && <p className="catalog-loading">공정룸을 준비하고 있어…</p>}{error && <p className="catalog-error">{error}</p>}
        <div className="room-grid">{scenarios.map((item)=><button key={item.id} type="button" className={`module-card ${focused?.id===item.id?'focused':''}`} onMouseEnter={()=>setFocusedId(item.id)} onFocus={()=>setFocusedId(item.id)} onClick={()=>onSelect(item.id)} aria-label={`${item.process} ${item.title} 시나리오 시작`}><span>{item.module_no} · {item.process}</span><b>{item.title}</b><small>{item.tagline}</small><i>ENTER ROOM ↗</i></button>)}</div>
      </section>}
      {hall && focused && <aside className="problem-bubble"><span>MISSION BRIEF · {focused.process}</span><b>{focused.tagline}</b><p>원인은 숨겨져 있어. 분포를 나누고 경쟁 가설을 세운 뒤, 최소 비용의 측정과 Holdout으로 반증해.</p></aside>}
    </section>
    <footer><p>교육용 합성 팹 · 실제 기업의 팹 배치·Recipe·Spec을 복제하지 않음</p><p>DATA → HYPOTHESIS → EVIDENCE → DECISION</p></footer>
  </main>
}
