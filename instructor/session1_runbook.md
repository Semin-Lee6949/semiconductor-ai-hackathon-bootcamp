# 1차 강의 강사용 Runbook — 120분

상세 실습 절차는 `student/01_FIRST_CLASS_HANDS_ON_MANUAL.md`, Telegram 복사·발송문은 `instructor/01_TELEGRAM_DELIVERY_SCRIPT.md`, 구간별 연결 멘트와 시간 지연 대응은 `instructor/SESSION1_SMOOTH_FLOW.md`를 사용한다. 이 문서는 강사의 시간·판단 기준만 요약한다.

## 시작 전

- 완성 CMP 데모 로컬·배포 URL 열기
- seaborn·ggplot2 Gallery와 `cmp_audit_gallery.png` 열기
- 실패 대비 Screenshot과 녹화본 준비
- GitHub 로그인, Fork, Push, Pages 권한 확인
- 교육장 Wi-Fi에서 OpenAI·GitHub·Google 접속 확인
- 수강생 20명의 과제 A/B 배정표 준비

## 진행 원칙

- 설명보다 완료 화면을 먼저 보여준다.
- 한 명의 로그인 오류로 전체 수업을 멈추지 않는다. 보조인력 또는 짝 실습으로 분리한다.
- 38분까지 버전 확인, 52분까지 Clone·자동점검, 67분까지 통계 감사, 95분까지 시각화, 106분까지 Push를 끝낸다.
- `✅` 15명 이상이면 다음 단계로 이동하고 나머지는 조별 파트너·보조강사가 복구한다.
- 설치 문제에 10분 이상 쓰지 않고 ZIP·GitHub 웹 편집 우회로로 실습을 계속한다.
- NotebookLM 결과물 제작보다 출처 등록과 공유 가능 여부를 먼저 확인한다.
- 결측·이상치 처리법을 먼저 나열하지 않는다. noisy CSV에서 실제 위치와 영향을 발견한 뒤 처리 선택지를 설명한다.
- ggplot2와 seaborn을 모두 보여주되 실습 코드는 Python·seaborn 하나로 통일한다.

## 시연 프롬프트

```text
AGENTS.md와 README.md를 먼저 읽어라.
지금은 코드를 수정하지 말고 이 데모의 입력, 데이터 감사,
기준모델, 개선모델, 브라우저 시뮬레이션, 테스트 흐름을 설명하라.
확인되지 않은 반도체 공정 사실을 추가하지 마라.
```

```text
CMP 데모에 Pad Age 경고를 추가하려 한다.
수정 전에 성공 기준과 최소 변경 파일을 제안하라.
동의 후에만 구현하고 unittest와 로컬 빌드를 실행하라.
```

## 종료 확인

- 저장소 URL·초기 Pages URL 수집
- `PLAN.md`에 사용자·KPI·가설·완료조건 존재
- 첫 데이터 감사 Commit 존재
- 8/17·8/19·8/20 마감 재안내
- 후보 주제 2개와 사용자 결정 1개 기록
