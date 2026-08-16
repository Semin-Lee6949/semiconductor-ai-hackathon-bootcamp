import { ContactShadows, Html } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef, useState } from 'react'
import { MathUtils, Vector3 } from 'three'
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
  [-5.6, 0, 1.5], [-3.4, 0, 1.52], [-1.2, 0, 1.38], [1.15, 0, 1.46], [3.55, 0, -.08], [3.55, 0, -2.25],
]

const ACTION_DURATIONS = [650, 1850, 1550, 1950, 2250] as const
const ACTION_LABELS = ['출입 확인 중…', '손과 손목을 세정 중…', '마스크를 착용 중…', '방진복과 장갑을 착용 중…', '에어샤워 가동 중…'] as const

function CameraRig({ step, hall, cinematic, reducedMotion }: { step: number; hall: boolean; cinematic: boolean; reducedMotion: boolean }) {
  const { camera } = useThree()
  const targetPosition = useMemo(() => hall ? new Vector3(0, 5.3, 10.8) : cinematic ? new Vector3(6.15, 2.65, 3.7) : new Vector3(6.8, 4.2, 8.5), [cinematic, hall])
  const targetLook = useMemo(() => hall ? new Vector3(0, 1.1, -2.2) : cinematic ? new Vector3(3.55, 1.12, -.7) : new Vector3(ENTRY_POSITIONS[step][0], 1, ENTRY_POSITIONS[step][2]), [cinematic, hall, step])

  useEffect(() => {
    if (!reducedMotion) return
    camera.position.copy(targetPosition)
    camera.lookAt(targetLook)
    camera.updateProjectionMatrix()
  }, [camera, reducedMotion, targetLook, targetPosition])

  useFrame((_, delta) => {
    if (reducedMotion) return
    camera.position.lerp(targetPosition, 1 - Math.exp(-delta * (cinematic ? .72 : 2.8)))
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

function SinkStation({ active, running }: { active: boolean; running: boolean }) {
  const water = useRef<Mesh>(null)
  useFrame(({ clock }) => { if (water.current && running) water.current.scale.y = .8 + Math.sin(clock.elapsedTime * 10) * .14 })
  return <group position={[-3.4,0,.6]}>
    <mesh position={[0,.74,0]}><boxGeometry args={[1.5,.25,1]}/><meshStandardMaterial color="#dbe7e7" metalness={.65} roughness={.18}/></mesh>
    <mesh position={[0,.84,0]}><cylinderGeometry args={[.55,.42,.18,30]}/><meshStandardMaterial color="#88aeb3" metalness={.8}/></mesh>
    <mesh position={[0,1.28,-.35]}><torusGeometry args={[.32,.07,12,28,Math.PI]}/><meshStandardMaterial color="#54777d" metalness={.8}/></mesh>
    <mesh ref={water} visible={running} position={[0,1.02,-.08]}><cylinderGeometry args={[.025,.04,.55,10]}/><meshStandardMaterial color="#5de9ff" emissive="#008da3" emissiveIntensity={1.2} transparent opacity={.7}/></mesh>
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

function AirShower({ active, running, entryOpen, exitOpen }: { active: boolean; running: boolean; entryOpen: boolean; exitOpen: boolean }) {
  const particles = useRef<Group>(null)
  const entryLeft = useRef<Mesh>(null)
  const entryRight = useRef<Mesh>(null)
  const exitLeft = useRef<Mesh>(null)
  const exitRight = useRef<Mesh>(null)
  useFrame(({ clock }, delta) => {
    if (particles.current && running) particles.current.rotation.y = clock.elapsedTime * 2.4
    const moveDoor = (door: Mesh | null, angle: number) => { if (door) door.rotation.y = MathUtils.lerp(door.rotation.y, angle, 1-Math.exp(-delta*1.15)) }
    moveDoor(entryLeft.current, entryOpen ? -1.28 : 0)
    moveDoor(entryRight.current, entryOpen ? 1.28 : 0)
    moveDoor(exitLeft.current, exitOpen ? 1.28 : 0)
    moveDoor(exitRight.current, exitOpen ? -1.28 : 0)
  })
  return <group position={[3.55,0,.1]}>
    <mesh position={[0,1.65,-.15]}><boxGeometry args={[2.25,3.3,1.8]}/><meshStandardMaterial color="#68858b" metalness={.72} roughness={.23} transparent opacity={.42}/></mesh>
    <mesh ref={entryLeft} position={[-.53,1.65,.78]}><boxGeometry args={[1.02,3.1,.08]}/><meshStandardMaterial color="#a8f3f1" transparent opacity={.48}/></mesh>
    <mesh ref={entryRight} position={[.53,1.65,.78]}><boxGeometry args={[1.02,3.1,.08]}/><meshStandardMaterial color="#a8f3f1" transparent opacity={.48}/></mesh>
    <mesh ref={exitLeft} position={[-.53,1.65,-1.08]}><boxGeometry args={[1.02,3.1,.08]}/><meshStandardMaterial color="#79dadd" metalness={.28} transparent opacity={.58}/></mesh>
    <mesh ref={exitRight} position={[.53,1.65,-1.08]}><boxGeometry args={[1.02,3.1,.08]}/><meshStandardMaterial color="#79dadd" metalness={.28} transparent opacity={.58}/></mesh>
    <group ref={particles}>{Array.from({length:24},(_,i) => { const a=(i/24)*Math.PI*2; return <mesh key={i} visible={running} position={[Math.cos(a)*.65,.4+(i%6)*.45,Math.sin(a)*.5]}><sphereGeometry args={[.025,6,6]}/><meshBasicMaterial color="#aaffff"/></mesh> })}</group>
    <Html position={[0,3.75,0]} center><span className={`lobby-station-tag ${active ? 'active' : ''}`}>04 · AIR SHOWER</span></Html>
  </group>
}

function Rookie({ step, acting, cinematic, reducedMotion }: { step: number; acting: boolean; cinematic: boolean; reducedMotion: boolean }) {
  const root = useRef<Group>(null)
  const body = useRef<Group>(null)
  const head = useRef<Group>(null)
  const leftArm = useRef<Group>(null)
  const rightArm = useRef<Group>(null)
  const leftForearm = useRef<Group>(null)
  const rightForearm = useRef<Group>(null)
  const leftHand = useRef<Mesh>(null)
  const rightHand = useRef<Mesh>(null)
  const leftLeg = useRef<Group>(null)
  const rightLeg = useRef<Group>(null)
  const actionStarted = useRef(0)
  const target = useMemo(() => new Vector3(...ENTRY_POSITIONS[step]), [step])

  useEffect(() => { if (acting) actionStarted.current = performance.now() }, [acting, step])

  useFrame(({ clock }, delta) => {
    if (!root.current || !body.current) return
    const distance = root.current.position.distanceTo(target)
    const walking = distance > .055 && !acting
    const phase = clock.elapsedTime * (cinematic ? 3.35 : 7.2)
    const damp = (current: number, next: number, speed = 9) => MathUtils.lerp(current, next, 1 - Math.exp(-delta * speed))
    const pose = (part: Group | null, x: number, z: number, speed = 9) => {
      if (!part) return
      part.rotation.x = damp(part.rotation.x, x, speed)
      part.rotation.z = damp(part.rotation.z, z, speed)
    }

    if (reducedMotion) root.current.position.copy(target)
    else root.current.position.lerp(target, 1 - Math.exp(-delta * (cinematic ? .62 : 2.5)))

    if (walking) {
      const direction = target.clone().sub(root.current.position)
      root.current.rotation.y = damp(root.current.rotation.y, Math.atan2(direction.x, direction.z), 6)
    } else if (!(step === 4 && acting)) {
      root.current.rotation.y = damp(root.current.rotation.y, Math.PI, 5)
    }

    const gait = reducedMotion ? 0 : Math.sin(phase)
    const idle = reducedMotion ? 0 : Math.sin(clock.elapsedTime * 2.1)
    body.current.position.y = damp(body.current.position.y, walking ? Math.abs(Math.sin(phase * 2)) * (cinematic ? .035 : .055) : idle * .012, 12)
    body.current.rotation.x = damp(body.current.rotation.x, walking ? (cinematic ? .045 : .08) : 0, 8)
    if (head.current) head.current.rotation.y = damp(head.current.rotation.y, walking ? gait * .055 : idle * .025, 7)

    pose(leftLeg.current, walking ? gait * (cinematic ? .34 : .48) : 0, walking ? -.025 : 0)
    pose(rightLeg.current, walking ? -gait * (cinematic ? .34 : .48) : 0, walking ? .025 : 0)

    let leftArmX = walking ? -gait * (cinematic ? .24 : .38) : 0
    let rightArmX = walking ? gait * (cinematic ? .24 : .38) : 0
    let leftArmZ = -.08
    let rightArmZ = .08
    let forearmX = walking ? -.18 : 0
    const actionTime = Math.max(0, (performance.now() - actionStarted.current) / 1000)

    if (acting && step === 1) {
      leftArmX = -1.12
      rightArmX = -1.12
      leftArmZ = -.18
      rightArmZ = .18
      forearmX = -1.02
      body.current.rotation.x = damp(body.current.rotation.x, -.17, 7)
      if (leftHand.current && rightHand.current && !reducedMotion) {
        const rub = Math.sin(actionTime * 13) * .055
        leftHand.current.position.x = -.04 + rub
        rightHand.current.position.x = .04 - rub
        leftHand.current.rotation.y = actionTime * 5
        rightHand.current.rotation.y = -actionTime * 5
      }
    } else if (acting && step === 2) {
      leftArmX = -1.16
      rightArmX = -1.16
      leftArmZ = -.22
      rightArmZ = .22
      forearmX = -1.34
    } else if (acting && step === 3) {
      leftArmZ = -1.32
      rightArmZ = 1.32
      leftArmX = -.08
      rightArmX = -.08
      forearmX = 0
    } else if (acting && step === 4) {
      leftArmZ = -.72
      rightArmZ = .72
      leftArmX = -.08
      rightArmX = -.08
      forearmX = -.08
      if (!reducedMotion) root.current.rotation.y += delta * .72
    }

    pose(leftArm.current, leftArmX, leftArmZ)
    pose(rightArm.current, rightArmX, rightArmZ)
    pose(leftForearm.current, forearmX, -.02)
    pose(rightForearm.current, forearmX, .02)
  })

  const masked = step > 2 || (step === 2 && acting)
  const gowned = step > 3 || (step === 3 && acting)
  const cloth = gowned ? '#f4fbfb' : '#26a8b2'
  const glove = gowned ? '#d9ffff' : '#e6b991'

  return <group ref={root} position={ENTRY_POSITIONS[0]} rotation={[0,Math.PI,0]} scale={.76}>
    <group ref={body}>
      <group ref={leftLeg} position={[-.2,.72,0]}>
        <mesh position={[0,-.35,0]}><capsuleGeometry args={[.13,.45,6,10]}/><meshStandardMaterial color="#213f48"/></mesh>
        <mesh position={[0,-.72,.09]} scale={[1,.55,1.55]}><sphereGeometry args={[.16,12,8]}/><meshStandardMaterial color="#18333b"/></mesh>
      </group>
      <group ref={rightLeg} position={[.2,.72,0]}>
        <mesh position={[0,-.35,0]}><capsuleGeometry args={[.13,.45,6,10]}/><meshStandardMaterial color="#213f48"/></mesh>
        <mesh position={[0,-.72,.09]} scale={[1,.55,1.55]}><sphereGeometry args={[.16,12,8]}/><meshStandardMaterial color="#18333b"/></mesh>
      </group>
      <mesh position={[0,.82,0]}><capsuleGeometry args={[.25,.28,6,12]}/><meshStandardMaterial color={gowned ? '#e6f5f4' : '#213f48'}/></mesh>
      <mesh position={[0,1.33,0]} scale={[1,.95,.7]}><capsuleGeometry args={[.43,.48,7,14]}/><meshStandardMaterial color={cloth}/></mesh>
      {gowned && <mesh position={[0,1.23,-.02]} scale={[1.06,1.18,.78]}><capsuleGeometry args={[.44,.46,7,14]}/><meshStandardMaterial color="#f4fbfb" transparent opacity={.94}/></mesh>}

      <group ref={leftArm} position={[-.48,1.56,0]}>
        <mesh position={[0,-.29,0]}><capsuleGeometry args={[.11,.36,6,10]}/><meshStandardMaterial color={cloth}/></mesh>
        <group ref={leftForearm} position={[0,-.57,0]}><mesh position={[0,-.25,0]}><capsuleGeometry args={[.1,.3,6,10]}/><meshStandardMaterial color={cloth}/></mesh><mesh ref={leftHand} position={[0,-.5,0]} scale={[.8,1.1,.65]}><sphereGeometry args={[.14,12,8]}/><meshStandardMaterial color={glove}/></mesh></group>
      </group>
      <group ref={rightArm} position={[.48,1.56,0]}>
        <mesh position={[0,-.29,0]}><capsuleGeometry args={[.11,.36,6,10]}/><meshStandardMaterial color={cloth}/></mesh>
        <group ref={rightForearm} position={[0,-.57,0]}><mesh position={[0,-.25,0]}><capsuleGeometry args={[.1,.3,6,10]}/><meshStandardMaterial color={cloth}/></mesh><mesh ref={rightHand} position={[0,-.5,0]} scale={[.8,1.1,.65]}><sphereGeometry args={[.14,12,8]}/><meshStandardMaterial color={glove}/></mesh></group>
      </group>

      <mesh position={[0,1.77,0]}><cylinderGeometry args={[.12,.14,.18,12]}/><meshStandardMaterial color="#d59d73"/></mesh>
      <group ref={head} position={[0,2.08,0]}>
        {gowned && <mesh position={[0,0,-.06]} scale={[1.2,1.18,1.06]}><sphereGeometry args={[.43,18,14]}/><meshStandardMaterial color="#f7ffff"/></mesh>}
        <mesh><sphereGeometry args={[.38,18,14]}/><meshStandardMaterial color="#e6b991"/></mesh>
        {!gowned && <mesh position={[0,.2,-.03]} scale={[1.02,.55,1.02]}><sphereGeometry args={[.39,16,10]}/><meshStandardMaterial color="#263b43"/></mesh>}
        <mesh position={[-.14,.05,.34]}><sphereGeometry args={[.035,8,6]}/><meshBasicMaterial color="#152b32"/></mesh>
        <mesh position={[.14,.05,.34]}><sphereGeometry args={[.035,8,6]}/><meshBasicMaterial color="#152b32"/></mesh>
        {gowned && <mesh position={[0,0,.345]}><torusGeometry args={[.34,.045,8,20]}/><meshStandardMaterial color="#cfe7e7"/></mesh>}
        {masked && <mesh position={[0,-.08,.36]} scale={[1.1,.58,.18]}><sphereGeometry args={[.31,14,10]}/><meshStandardMaterial color="#a8eff1"/></mesh>}
      </group>
    </group>
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

function LobbyScene({ step, acting, hall, cinematic, scenarios, onSelect, reducedMotion }: { step: number; acting: boolean; hall: boolean; cinematic: boolean; scenarios: ScenarioSummary[]; onSelect: (id: string) => void; reducedMotion: boolean }) {
  return <Canvas camera={{position:[6.8,4.2,8.5],fov:42}} dpr={[1,1.5]} frameloop={reducedMotion ? 'demand' : 'always'}>
    <color attach="background" args={[hall ? '#071c23' : '#dbe8e8']}/>
    <ambientLight intensity={hall ? 1.1 : 2.1}/><directionalLight position={[5,9,6]} intensity={hall ? 2.2 : 3.2}/>
    <FacilityShell hall={hall}/><CameraRig step={step} hall={hall} cinematic={cinematic} reducedMotion={reducedMotion}/>
    {!hall && <><SinkStation active={step===1} running={step===1 && acting}/><MaskStation active={step===2}/><GownStation active={step===3}/><AirShower active={step===4||cinematic} running={step===4 && acting} entryOpen={step===4&&!acting} exitOpen={cinematic}/><Rookie step={step} acting={acting} cinematic={cinematic} reducedMotion={reducedMotion}/></>}
    {hall && scenarios.map((item,index)=><RoomDoor key={item.id} item={item} index={index} onSelect={() => onSelect(item.id)}/>)}
    <ContactShadows position={[0,.01,0]} opacity={hall ? .32 : .18} scale={18} blur={2.8} far={8}/>
  </Canvas>
}

export function CleanroomLobby({ scenarios, loading, error, onSelect }: { scenarios: ScenarioSummary[]; loading: boolean; error: string; onSelect: (id: string) => void }) {
  const [step,setStep] = useState(0)
  const [acting,setActing] = useState(false)
  const [moving,setMoving] = useState(false)
  const [cinematic,setCinematic] = useState(false)
  const [hallEntered,setHallEntered] = useState(false)
  const [focusedId,setFocusedId] = useState('photo-cd-drift')
  const actionTimer = useRef<number | null>(null)
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const focused = scenarios.find((item)=>item.id===focusedId) ?? scenarios[0]
  const hall = hallEntered
  useEffect(() => () => {
    if (actionTimer.current !== null) window.clearTimeout(actionTimer.current)
  }, [])

  const advance = () => {
    if (acting || moving || step >= 5) return
    setActing(true)
    actionTimer.current = window.setTimeout(() => {
      const nextStep = Math.min(5,step+1)
      setStep(nextStep)
      setActing(false)
      if (nextStep === 5 && !reducedMotion) {
        setCinematic(true)
        actionTimer.current = window.setTimeout(() => {
          setCinematic(false)
          setHallEntered(true)
          actionTimer.current = null
        }, 4400)
      } else if (nextStep === 5) {
        setHallEntered(true)
        actionTimer.current = null
      } else if (!reducedMotion) {
        setMoving(true)
        actionTimer.current = window.setTimeout(() => {
          setMoving(false)
          actionTimer.current = null
        }, 1250)
      } else actionTimer.current = null
    }, reducedMotion ? 180 : ACTION_DURATIONS[step])
  }

  return <main className={`cleanroom-lobby ${hall?'hall-open':''} ${cinematic?'cinematic-entry':''}`}>
    <header className="game-topbar"><div><b>VIRTUAL FAB</b><span>FACILITY 01 · SCHOLARBRIDGE</span></div><div><span>ACCESS</span><strong>{hall?'GRANTED':cinematic?'ENTERING':`${step}/4`}</strong></div></header>
    <section className="lobby-viewport" aria-label="가상 클린룸 입실 화면">
      <LobbyScene step={step} acting={acting} hall={hall} cinematic={cinematic} scenarios={scenarios} onSelect={onSelect} reducedMotion={reducedMotion}/>
      <div className="scanlines" aria-hidden="true"/>
      <div className="entry-progress" aria-label="클린룸 입실 진행 단계">{ENTRY_STEPS.map((item,index)=><div key={item.code} className={index<step?'done':index===step?'active':''}><span>{String(index+1).padStart(2,'0')}</span><b>{item.code}</b></div>)}</div>
      {step<5 && <section className={`guide-dialog ${acting||moving?'acting':''}`} aria-live="polite"><div className="guide-portrait"><span>{acting||moving?'···':'AI'}</span><b>SAFETY<br/>GUIDE</b></div><div><span>ENTRY PROTOCOL {String(step+1).padStart(2,'0')}</span><h1>{ENTRY_STEPS[step].title}</h1><p>{ENTRY_STEPS[step].copy}</p><button type="button" onClick={advance} disabled={acting||moving} aria-busy={acting||moving}>{moving?'다음 스테이션으로 이동 중…':acting?ACTION_LABELS[step]:ENTRY_STEPS[step].action}<b>{acting||moving?'●':'→'}</b></button></div></section>}
      {cinematic && <section className="final-entry-cue" aria-live="polite"><h1>이제, 네가 증명할 차례야.</h1><p>공정 데이터가 기다리고 있다.</p></section>}
      {hall && <section className="mission-console"><header><div><span>CLEANROOM ACCESS GRANTED</span><h1>사건이 기다리는 공정룸을 선택해.</h1></div><p>문을 열면 60–90분의 제한시간이 시작돼.<br/>정답이 아니라 증거의 순서를 보여줘.</p></header>
        {loading && <p className="catalog-loading">공정룸을 준비하고 있어…</p>}{error && <p className="catalog-error">{error}</p>}
        <div className="room-grid">{scenarios.map((item)=><button key={item.id} type="button" className={`module-card ${focused?.id===item.id?'focused':''}`} onMouseEnter={()=>setFocusedId(item.id)} onFocus={()=>setFocusedId(item.id)} onClick={()=>onSelect(item.id)} aria-label={`${item.process} ${item.title} 시나리오 시작`}><span>{item.module_no} · {item.process}</span><b>{item.title}</b><small>{item.tagline}</small><i>ENTER ROOM ↗</i></button>)}</div>
      </section>}
      {hall && focused && <aside className="problem-bubble"><span>MISSION BRIEF · {focused.process}</span><b>{focused.tagline}</b><p>원인은 숨겨져 있어. 분포를 나누고 경쟁 가설을 세운 뒤, 최소 비용의 측정과 Holdout으로 반증해.</p></aside>}
    </section>
    <footer><p>교육용 합성 팹 · 실제 기업의 팹 배치·Recipe·Spec을 복제하지 않음</p><p>DATA → HYPOTHESIS → EVIDENCE → DECISION</p></footer>
  </main>
}
