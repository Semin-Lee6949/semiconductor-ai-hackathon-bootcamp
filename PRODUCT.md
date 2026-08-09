# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

위험한 설치 의존성을 늘리지 않는 정적 HTML·CSS·JavaScript. GitHub Pages에서 배포한다.

## Users

- 반도체 소자·공정·설비·양산기술 직무를 준비하는 수강생 약 20명
- 120분 오프라인 수업을 진행하는 강사와 보조강사
- 프로젝터, 노트북, 휴대폰을 오가며 설치 명령과 실습 순서를 확인한다.

## Product Purpose

반도체 현장의 질문을 데이터 감사, 시각화, AI 검증, 재현 가능한 결과물로 전환하는 첫 강의 안내서다. 수강생이 모델 이름보다 사용자·신호·의사결정을 먼저 정의하고, 수업 종료 시 자신의 프로젝트 후보를 남긴 뒤 일주일 동안 독립적인 성과물로 완성하면 성공이다.

## Positioning

AI 기능을 나열하지 않고 `문제 → 전공 원리·Governing equation → 데이터 → 상관·대안가설 → 의사결정 → 리포트`라는 엔지니어링 증거 사슬을 직접 완성하게 한다.

## Operating Context

- 수업 전 문제발견 질문지를 10분 작성한다.
- 수업 중 Telegram으로 설치 단계를 하나씩 전달한다.
- 합성 데이터로 결측·이상치·편중을 감사하고 seaborn 그래프를 만든다.
- Antigravity의 원문 조사 결과를 근거카드로 남기고, Claude Code 또는 Codex의 변경을 사람이 diff와 테스트로 검증한다.
- 수업 말미에 문제정의를 다시 작성하고 GitHub Pages 결과를 제출한다.

## Capabilities and Constraints

- 첫 강의의 분 단위 Lecture Map과 설치·실습 명령을 제공한다.
- 플라즈마 RF matcher, Vpp, Vdc와 박막 품질 관계는 문제발견 예시로만 사용한다.
- 실제 회사 데이터·내부 Spec·장비 로그·고객정보·개인정보·API Key를 사용하지 않는다.
- 상관관계를 인과관계로 단정하지 않으며 대안 가설을 최소 하나 검토한다.
- AI가 제시한 물리식과 해석은 교재·논문·공식 문서로 사람이 확인한다.

## Evidence on Hand

- `COURSE_PLAN.md`: 일정과 성공 기준
- `student/00_PROBLEM_DISCOVERY_QUESTIONNAIRE.md`: 문제발견 질문지
- `student/01_FIRST_CLASS_HANDS_ON_MANUAL.md`: 설치부터 Pages까지 실습서
- `instructor/SESSION1_SMOOTH_FLOW.md`: 120분 진행표
- `lessons/01_DATA_QUALITY_AND_VISUALIZATION.md`: 데이터 품질·시각화 수업
- 교육용 합성 데이터와 자동 테스트

## Product Principles

1. 문제와 사용자 결정을 모델보다 먼저 둔다.
2. 데이터 품질을 분석보다 먼저 확인한다.
3. 상관·인과·대안 설명을 구분한다.
4. AI 출력은 근거·diff·테스트로 검증한다.
5. 실제 회사정보 대신 재현 가능한 합성 증거를 남긴다.

## Accessibility & Inclusion

키보드 탐색, 충분한 대비, 동작 줄이기 설정, 모바일 가독성을 지원한다. 명령은 복사 가능한 텍스트로 제공한다.
