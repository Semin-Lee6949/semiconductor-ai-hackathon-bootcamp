# Virtual Fab R3F 캐릭터 개선 바톤 — 2026-08-17

> 대상: GitHub에서 저장소를 받은 뒤 Codex CLI로 가상 반도체 실험실의 3D 캐릭터를 개선하는 작업
>
> 저장소: `https://github.com/waterfirst/semiconductor-ai-hackathon-bootcamp`
>
> 앱: `virtual-fab-app/`

## 0. 가장 먼저 읽을 결론

1. 이 앱은 이미 `@react-three/fiber`를 사용한다. 새 3D 엔진으로 교체하는 작업이 아니다.
2. 현재 조합은 React `19.2.8`, Fiber `9.7.0`, Three.js `0.185.1`, Drei `10.7.8`이다.
3. Fiber 공식 호환 지침상 Fiber 9는 React 19와 짝을 이룬다.
4. 첫 구현은 외부 GLB를 추가하지 말고 기존 절차형 캐릭터를 개선한다.
5. 캐릭터 개선은 `feat/vfab-r3f-character` 브랜치에서만 진행한다.
6. P0 데이터·채점 결함이 아직 남아 있으므로 캐릭터 브랜치를 `main`에 병합하거나 운영 서버에 배포하지 않는다.
7. `vfab_assets/UPGRADE_SPEC_v2.md`는 P0-A·P0-B 완료 전 열거나 적용하지 않는다.

공식 참고:

- React Three Fiber: <https://github.com/pmndrs/react-three-fiber>
- R3F 문서: <https://r3f.docs.pmnd.rs/>
- Codex CLI: <https://developers.openai.com/codex/cli>
- Codex `AGENTS.md`: <https://developers.openai.com/codex/guides/agents-md>

## 1. GitHub pull 전 안전 확인

### 새 PC에서 처음 받는 경우

```bash
cd ~/python
git clone https://github.com/waterfirst/semiconductor-ai-hackathon-bootcamp.git
cd semiconductor-ai-hackathon-bootcamp
git status -sb
```

### 이미 저장소가 있는 경우

로컬 작업을 임의로 버리거나 `git reset --hard` 하지 않는다.

```bash
cd ~/python/semiconductor-ai-hackathon-bootcamp
git status -sb
git fetch origin
git log --oneline --decorate --graph -8 --all
git pull --ff-only origin main
```

`git pull --ff-only`가 거절되면 강제로 합치지 말고 로컬 변경과 원격 차이를 먼저 확인한다.

```bash
git rev-list --left-right --count main...origin/main
git diff --stat
```

## 2. 시각 작업용 브랜치 만들기

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/vfab-r3f-character
```

이미 같은 이름의 로컬 브랜치가 있다면 새로 만들지 않는다.

```bash
git switch feat/vfab-r3f-character
```

## 3. 의존성 설치와 버전 확인

이 저장소에는 필요한 패키지가 이미 선언되어 있으므로 먼저 잠금파일 그대로 설치한다.

```bash
cd virtual-fab-app
npm ci
npm ls react three @react-three/fiber @react-three/drei --depth=0
```

정상 기대값:

```text
react@19.2.8
three@0.185.1
@react-three/fiber@9.7.0
@react-three/drei@10.7.8
```

따라서 평상시에는 다음 설치 명령을 다시 실행하지 않는다.

```bash
# 현재 저장소에서는 불필요함
npm install three @types/three @react-three/fiber @react-three/drei
```

`package.json`에서 의존성이 실제로 사라진 경우에만 위 명령을 사용하고, 버전 변경과 `package-lock.json` 변경 이유를 커밋에 기록한다.

## 4. Codex CLI 시작 명령

저장소 루트에서 실행하는 대화형 방식이 권장된다. Codex는 시작할 때 루트의 `AGENTS.md`를 읽는다.

```bash
cd ~/python/semiconductor-ai-hackathon-bootcamp
codex -C . --search
```

캐릭터 참고 이미지를 함께 줄 경우:

```bash
codex -C . --search -i /절대경로/character-reference.png
```

Codex 입력창에 아래 프롬프트를 그대로 넣는다.

```text
BATON_VIRTUAL_FAB_R3F_CHARACTER_2026-08-17.md와 AGENTS.md를 먼저 읽어라.
현재 virtual-fab-app의 FabScene.tsx와 CleanroomLobby.tsx에서 캐릭터 구현과 모바일 렌더링을 조사하라.

바로 코드를 수정하지 말고 먼저 캐릭터 디자인 방향 3가지를 제시하라.
각 방향마다 실루엣, 방진복 디테일, 애니메이션, 성능, 구현 위험을 비교하고 하나를 추천하라.
내가 방향을 선택한 뒤에만 구현하라.

구현 범위는 3D 캐릭터와 그 접지·가독성에 한정한다.
시나리오, CSV, AI 문답, 점수, FastAPI 계약은 변경하지 마라.
외부 GLB와 신규 런타임 의존성은 첫 패스에서 추가하지 마라.
vfab_assets/UPGRADE_SPEC_v2.md는 열지 마라.

PC 1440x1000과 Pixel 7 크기를 모두 Playwright로 검증하고, prefers-reduced-motion을 보존하라.
빌드·pytest·관련 E2E와 impeccable detector를 실행하라.
P0 데이터·채점 완료 전 main 병합과 운영 배포는 하지 마라.
```

한 번에 비대화형으로 분석만 시킬 경우:

```bash
codex exec -C . --search --sandbox workspace-write \
  "BATON_VIRTUAL_FAB_R3F_CHARACTER_2026-08-17.md를 읽고 현재 캐릭터 구조를 감사하라. 코드는 수정하지 말고 디자인 방향 3개, 추천안, 수정 파일, 성능 위험, 테스트 계획만 보고하라. UPGRADE_SPEC_v2.md는 열지 마라."
```

`--dangerously-bypass-approvals-and-sandbox` 또는 `--yolo`는 사용하지 않는다.

## 5. 현재 캐릭터의 실제 구조

주요 구현은 `virtual-fab-app/src/FabScene.tsx`의 `FabOperator`다.

- 외부 3D 모델 없이 box/cylinder/sphere geometry로 조립한 절차형 캐릭터
- `useFrame`에서 목표 스테이션으로 이동
- 이동 방향으로 회전
- 팔·다리 교차 보행
- 정지 시 미세한 idle 동작
- 머리 위 `Html` 대화 카드
- 전체 스케일 `.78`

현재 장점:

- 추가 에셋 다운로드가 없다.
- 상태와 이동 로직이 단순하고 재현 가능하다.
- 저사양 모바일에서 상대적으로 안전하다.
- 방진복 색과 바이저가 서비스 색상과 연결된다.

현재 한계:

- 몸통·팔·다리가 직육면체 중심이라 장난감 블록처럼 보인다.
- 어깨·팔꿈치·무릎 관절이 분리되지 않아 보행이 뻣뻣하다.
- 손·신발·후드·마스크·장갑의 실루엣 구분이 약하다.
- 상체와 골반의 반대 회전이 없어 무게감이 부족하다.
- 스테이션 근처 정지 시 발이 바닥에 미끄러지는 느낌이 있다.
- 캐릭터의 그림자와 바닥 접촉감이 약하다.
- 모바일에서는 3D 장면보다 데이터 작업이 우선이므로 디테일을 무한히 올릴 수 없다.

`CleanroomLobby.tsx`에도 입실 절차용 사람형 캐릭터와 단계 애니메이션이 있다. 두 캐릭터의 외관을 완전히 별개로 만들지 말고 색·후드·바이저·장갑의 공통 토큰을 사용한다.

## 6. 먼저 제시할 디자인 방향 3개

Codex는 구현 전에 다음 3개 방향을 간단한 ASCII 구조 또는 정지 화면 설명과 함께 제시한다.

### 방향 A — Procedural Cleanroom Rookie · 권장

- 현재 geometry 기반을 유지
- capsule/cylinder/sphere를 조합해 둥근 관절과 사람 실루엣 구현
- 후드, 투명 바이저, 마스크, 가슴 ID, 장갑, 덧신을 레이어로 구분
- 상체·골반·팔꿈치·무릎 그룹을 계층화
- 이동, idle, 가리키기, 데이터 확인 동작 구현
- 신규 에셋과 신규 패키지가 없어 가장 안전함

### 방향 B — Compact GLB Operator

- 라이선스가 명확한 자체 GLB 캐릭터 사용
- `useGLTF`, `useAnimations`, `Suspense`, `useGLTF.preload` 사용
- 자연스러운 스키닝 애니메이션 가능
- 모델·텍스처 용량, 라이선스, 로딩 실패, 모바일 메모리 위험이 있음
- P0 완료 후 2차 개선 후보로만 둠

### 방향 C — Holographic Training Avatar

- 반투명 교육용 아바타와 단순한 인간 실루엣
- 실제 작업자 복제 위험이 작고 미래형 UI와 어울림
- 홀로그램 효과가 과하면 공정 데이터보다 시각효과가 앞설 위험이 있음
- 포스트프로세싱 없이 emissive material만 사용해야 함

기본 추천은 **방향 A**다.

## 7. 선택 후 구현 범위

### 7.1 컴포넌트 분리

권장 구조:

```text
virtual-fab-app/src/
  scene/
    FabOperator.tsx
    CleanroomAvatarParts.tsx
    characterMotion.ts
```

- `FabScene.tsx`는 장면 구성과 스테이션 배치에 집중한다.
- `FabOperator.tsx`는 캐릭터 렌더링과 동작만 담당한다.
- 공통 색·치수는 `CleanroomAvatarParts.tsx`에 둔다.
- 프레임 독립적인 이동·보간 계산은 `characterMotion.ts`로 분리해 테스트 가능하게 한다.

컴포넌트가 오히려 짧은 코드를 분산한다면 무리하게 파일을 늘리지 않는다.

### 7.2 캐릭터 계층

최소 계층:

```text
operatorRoot
  headingRoot
    pelvis
      torso
        chestBadge
        hood
          head
          mask
          visor
        leftShoulder
          leftUpperArm
            leftElbow
              leftForearm
                leftGlove
        rightShoulder ...
      leftHip
        leftUpperLeg
          leftKnee
            leftLowerLeg
              leftBoot
      rightHip ...
```

회전축이 관절 위치에 오도록 mesh의 중심과 group의 pivot을 구분한다.

### 7.3 동작 상태

최소 동작:

- `idle`: 호흡, 작은 고개 움직임, 과도하지 않은 체중 이동
- `walk`: 골반 상하 이동, 상체 반대 회전, 팔·다리 교차, 발바닥 접지
- `inspect`: 데이터/웨이퍼를 내려다보는 자세
- `point`: 활성 스테이션을 한 손으로 가리키는 자세
- `confirm`: 검증 단계에서 짧게 고개를 끄덕이는 자세

동작은 현재 `stageIndex`와 이동 여부로 결정한다. 게임 로직이나 서버 상태를 새로 만들지 않는다.

### 7.4 R3F 구현 규칙

- `Canvas`, `useFrame`, React component 구조를 유지한다.
- `useFrame` 안에서 React `setState`를 매 프레임 호출하지 않는다.
- 시간 기반 애니메이션은 `delta` 또는 `clock.elapsedTime`으로 계산한다.
- 이동 보간은 프레임률에 독립적인 지수 보간을 유지한다.
- 반복적으로 생성되는 `Vector3`는 ref 또는 memo로 재사용해 프레임당 할당을 줄인다.
- 캐릭터 mesh에 필요한 범위만 `castShadow`를 적용한다.
- 바닥은 `receiveShadow`; ContactShadows는 낮은 opacity와 제한된 scale을 유지한다.
- 모바일 DPR 상한을 올리지 않는다.
- 포스트프로세싱, 실시간 반사, 물리엔진은 추가하지 않는다.
- 사용자 입력과 HTML 작업창의 접근성을 3D 연출보다 우선한다.
- `prefers-reduced-motion`에서는 보행 과장, idle 흔들림, 시네마틱을 줄인다.

## 8. 외부 GLB를 나중에 사용할 때의 조건

첫 패스 완료 후에도 GLB가 필요하다고 사용자가 명시할 때만 진행한다.

필수 조건:

- 제작자와 상업적 이용 라이선스 기록
- 실제 회사 유니폼·로고·팹 배치 복제 금지
- GLB 1.5MB 이하 권장
- 캐릭터 5만 triangles 이하 권장
- 텍스처 최대 1024px, 가능하면 WebP/KTX2 검토
- idle/walk 애니메이션만 우선
- 로딩 중 fallback 제공
- 모델 로딩 실패 시 절차형 캐릭터로 fallback

Drei 기반 예시 구조:

```tsx
const { scene, animations } = useGLTF('/models/fab-rookie.glb')
const { actions } = useAnimations(animations, root)
useGLTF.preload('/models/fab-rookie.glb')
```

GLB를 JSX로 변환해야 할 때만 별도 개발 도구를 검토한다. 패키지를 추가하기 전에 이유와 번들 영향을 보고한다.

## 9. 시각 완료 기준

### 데스크톱

- 1440×1000, 브라우저 배율 100%에서 캐릭터 전신이 명확히 보인다.
- 캐릭터와 좌측 하단 피드백 카드가 겹치지 않는다.
- 오른쪽 데이터·프롬프트 작업창의 폭을 침범하지 않는다.
- 분할바 32%, 48%, 72%에서 캐릭터가 잘리거나 비정상 확대되지 않는다.
- 이동 후 발이 바닥에 떠 있거나 깊게 관통하지 않는다.
- 대화 카드가 캐릭터 머리와 장비 라벨을 과도하게 가리지 않는다.

### 모바일

- Pixel 7 크기에서 초기 렌더링과 스크롤이 멈추지 않는다.
- 3D는 상단 390px 영역 안에서 의미 있는 실루엣을 유지한다.
- 데이터·AI 작업창과 다음 단계 버튼은 정상 표시된다.
- 터치 스크롤과 OrbitControls가 충돌하지 않는다.
- 저동작 설정에서 불필요한 지속 애니메이션이 줄어든다.

### 시각 언어

- 교육용 합성 팹임이 분명하다.
- 반도체 방진복, 후드, 마스크, 장갑, 덧신이 구별된다.
- 청록·짙은 남청·백색·호박색 포인트의 기존 색 체계를 유지한다.
- 귀여운 캐릭터이되 장난감 로봇보다는 ‘신입 공정 엔지니어’로 읽혀야 한다.
- 실제 SK하이닉스 로고·유니폼을 복제하지 않는다.

## 10. 성능 완료 기준

- 신규 런타임 의존성 0개를 첫 목표로 한다.
- 기존보다 Canvas DPR 상한을 높이지 않는다.
- 모바일에서 평균 30fps 이상을 목표로 한다.
- 데스크톱 내장 그래픽에서 평균 50fps 이상을 목표로 한다.
- 캐릭터 개선 때문에 초기 전송량이 1.5MB 이상 증가하지 않는다.
- 콘솔 WebGL 오류와 React key/ref 경고가 0건이어야 한다.
- 메모리 누수를 막기 위해 이벤트·URL·타이머를 정리한다.

정확한 FPS 자동 측정 장치가 없다면 Chrome Performance 기록과 Playwright의 동작 완료 시간을 함께 남기고, 수치를 측정하지 않은 상태에서 달성했다고 쓰지 않는다.

## 11. 변경 금지 범위

캐릭터 브랜치에서 다음을 변경하지 않는다.

- `virtual-fab-app/backend/main.py`의 데이터·채점 로직
- CSV 스키마와 시나리오 seed
- AI API/BYOK와 프롬프트 계약
- 면접 PT 생성 로직
- `vfab_assets/answer_key_*.json`
- `vfab_assets/generate_photo_cd.py`
- `vfab_assets/UPGRADE_SPEC_v2.md`
- 아래 무관 작업물
  - `artifacts/data_quality/cmp_audit_gallery.png`
  - `PLAN.md`
  - `design-directions/`
  - `proposals/preview/`
  - `submission/`
  - `virtual-fab-mvp/`

시각 작업 중 데이터 결함을 발견하면 수정하지 말고 별도 메모로 보고한다.

## 12. 테스트 명령

저장소 루트 기준:

```bash
cd virtual-fab-app
npm run build
PYTHONPATH=. .venv/bin/pytest -q
npx playwright test tests/e2e.spec.ts --project=desktop --reporter=line
npx playwright test tests/e2e.spec.ts --project=mobile --reporter=line
cd ..
node /home/waterfirst/.codex/skills/impeccable/scripts/detect.mjs --json virtual-fab-app
git diff --check
git status --short
```

다른 PC에 Impeccable skill이 없다면 해당 detector 명령은 생략하되 생략 사실을 보고한다.

필수 스크린샷:

- 데스크톱 첫 공정 단계, 분할 48%
- 데스크톱 분할 32%와 72%
- 캐릭터 이동 중 또는 이동 직후
- Pixel 7 첫 단계
- Pixel 7 데이터·AI 공동분석 단계
- reduced-motion 상태

## 13. 리뷰와 커밋

Codex 대화 안에서 구현 후:

```text
/review
```

터미널에서 변경 범위를 확인한다.

```bash
git diff --stat
git diff -- virtual-fab-app/src/FabScene.tsx \
  virtual-fab-app/src/CleanroomLobby.tsx \
  virtual-fab-app/src/scene \
  virtual-fab-app/tests/e2e.spec.ts
git status --short
```

허용된 파일만 stage한다. `git add .`는 사용하지 않는다.

```bash
git add virtual-fab-app/src/FabScene.tsx \
  virtual-fab-app/src/CleanroomLobby.tsx \
  virtual-fab-app/src/scene \
  virtual-fab-app/tests/e2e.spec.ts
git commit -m "feat: refine virtual fab operator character"
git push -u origin feat/vfab-r3f-character
```

실제로 수정되지 않은 경로는 `git add` 명령에서 뺀다.

## 14. 병합·배포 게이트

캐릭터 브랜치 구현과 리뷰는 진행할 수 있지만 다음 조건 전에는 `main`에 병합하거나 `virtual-fab.service`를 재시작하지 않는다.

- P0-A: seed 기반 PHOTO 데이터 생성기가 실제 API 세션과 연결됨
- 필수 UI: Tool/Lot/radius bin/slot/시간 그룹핑 구현
- P0-B: 7문항 서버 채점과 미끼 Tool 0점 규칙 구현
- 정답키가 프런트엔드·API 응답에 노출되지 않음
- 해당 백엔드 및 E2E 테스트 통과

게이트가 끝난 뒤에만 캐릭터 브랜치를 최신 `main`에 rebase하고 전체 회귀 테스트 후 병합한다.

```bash
git fetch origin
git switch feat/vfab-r3f-character
git rebase origin/main
# 전체 테스트 재실행
```

## 15. Codex 최종 보고 형식

Codex는 작업 종료 시 다음을 보고한다.

1. 선택한 디자인 방향과 선택 이유
2. 수정 파일 목록
3. R3F 구조 변경 요약
4. PC·모바일 전후 차이
5. 성능 측정값 또는 미측정 항목
6. 빌드·pytest·E2E 결과
7. 콘솔 오류 유무
8. 남은 위험과 GLB 2차 전환 필요성
9. 커밋 해시와 브랜치명
10. P0 미완료로 병합·배포를 보류했는지 여부

## 16. 현재 Git 인계 상태

2026-08-17 확인 당시:

- 로컬 `main`: `fee8df7` — 모바일 조사 단계 잠금 안내 및 캐시 개선
- 원격 `origin/main`: `703b6e6`
- 로컬이 원격보다 1커밋 앞선 상태였음
- 아래 무관 변경은 그대로 보존 중
  - `artifacts/data_quality/cmp_audit_gallery.png`
  - `PLAN.md`
  - `design-directions/`
  - `proposals/preview/`
  - `submission/`
  - `virtual-fab-mvp/`

따라서 다른 PC에서 pull하기 전에 이 바톤과 `fee8df7`가 원격에 push됐는지 확인한다.

