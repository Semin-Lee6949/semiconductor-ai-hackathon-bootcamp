# Project Plan

- 문제:
  Photo 공정조건 변화에 따라 CD와 결함 위험이 어떻게 달라지는지 분석하고,
  다음 DOE에서 우선 확인할 조건을 좁힌다.

- 실제 사용자:
  Photo 공정 엔지니어

- 사용자가 내릴 결정:
  어떤 PR tone과 Dose·Focus·PEB·현상조건 조합을
  다음 DOE에서 우선 검증할 것인가?

- 핵심 KPI:
  resist_line_cd_nm을 주 KPI로 사용하고,
  CDU, LER, Scum, Collapse, Defect, PASS/FAIL을 보조 품질지표로 확인한다.

- 제약조건·보안경계:
  교육용 합성 데이터만 사용한다.
  Holdout은 최종 검증 전까지 분석에 사용하지 않는다.

- 데이터 입력과 단위:
  A/train.csv
  Dose: mJ/cm²
  Focus: μm
  Thickness/CD/CDU/LER: nm
  Temperature: °C
  Develop time: s

- 지금 확인된 사실:
  805행 × 24열
  Positive PR 523개
  Negative PR 271개
  PR tone 결측 11개
  중복 5행
  결측 및 단위 오류 의심값 존재

- 아직 모르는 것:
  이상치 후보가 단순 입력 오류인지 실제 공정 이상인지
  PASS/FAIL의 정확한 판정 기준
  Tool/Lot 편중의 영향
  각 공정변수와 CD의 실제 관계

## 전공지식 키워드

- 핵심 변수:
  PR tone, Dose, Focus, PR thickness, PEB,
  Develop time, Developer concentration

- 관련 전공과목·물리법칙:
  Lithography, 광학, PR 반응, 고분자 재료,
  현상 반응, 공정통계

- 예상되는 방향성·단조성:
  단순한 단조 관계라고 가정하지 않는다.
  Dose·Focus·PR tone에 따라 CD 반응 방향이 달라질 가능성을 확인한다.

- 공정 순서·시간 관계:
  Coat → Softbake → Exposure → PEB → Develop → CD measurement

- 알려진 고장 메커니즘:
  Scum, Pattern collapse, CD deviation, CDU 증가, LER 증가

## 가설

1. 주가설:
   Dose, Focus, PEB, 현상조건이 resist line CD 변화와 관련될 수 있다.

2. 대안가설:
   관찰된 CD 차이가 PR tone, Tool, Lot,
   Field 위치 차이 때문에 나타났을 가능성이 있다.

3. 교란 가능성:
   결측치, 단위 오류, 이상치, Tool/Lot 편중,
   Positive/Negative PR 혼합이 관계를 왜곡할 수 있다.

## 실행 순서

1. 데이터 구조·단위·결측을 감사한다.
2. 전공지식으로 기대되는 관계를 적는다.
3. 단순 기준과 주가설·대안가설을 비교한다.
4. Holdout 또는 반례에서 다시 확인한다.
5. 결론·불확실성·다음 실험을 보고한다.

## AI와 티키타카할 질문

- 이 설명이 성립하려면 어떤 조건이 필요한가?
- 같은 관찰을 설명하는 반대 가설은 무엇인가?
- 어떤 그래프나 실험 결과가 이 가설을 반박하는가?
- 지금 답변에서 확인되지 않은 사실은 무엇인가?
- 내 전공지식과 충돌하는 부분을 표로 분리해라.

## 완료조건

- [ ] 데이터 감사
- [ ] 기준모델
- [ ] 분리된 평가
- [ ] 조작 기능 2개 이상
- [ ] 위험도·추천·추가 실험
- [ ] AI 기록과 한계
- [ ] Live URL

## 중단조건

- 데이터 정의·단위·출처를 확인할 수 없으면 결론을 내리지 않는다.
- 기밀정보가 필요하면 공개·합성 데이터로 범위를 바꾼다.
- Holdout 또는 반례에서 재현되지 않으면 원인으로 단정하지 않는다.
