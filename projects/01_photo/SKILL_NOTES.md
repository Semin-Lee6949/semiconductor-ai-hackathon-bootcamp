# Photo 프로젝트 전용 분석 메모

이 문서는 `projects/01_photo`의 교육용 합성 데이터와 현재 분석 범위에만 적용한다. 공통 분석 절차는 저장소 루트의 `SKILL.md`를 따르며, 아래 관찰 방향·수치·주의사항을 다른 공정이나 실제 recipe에 일반화하지 않는다.

## 그룹과 해석

- Positive PR과 Negative PR은 공정적으로 다른 그룹이므로 dose–CD 관계를 하나로 합쳐 해석하지 않는다.
- 현재 데이터에서는 normalized dose 증가에 따라 Positive PR의 CD는 감소하고 Negative PR의 CD는 증가하는 방향이 관찰됐다.
- 이 방향은 30회 반복 분할과 Lot 검증에서 확인했지만, 관찰적 조건부 관계이며 인과효과가 아니다.
- PR tone 결측은 `MISSING` 범주로 보존하되 실제 PR 물성 그룹처럼 해석하지 않는다.

## Tool과 데이터 품질

- Tool별 CD level 차이가 관찰되므로 Tool 효과를 보정하고, Tool condition/calibration 또는 Tool과 함께 변한 Lot·recipe 조건을 대안 설명으로 검토한다.
- T01/T02/T03 표본 수가 균등하지 않으므로 전체 평균이나 pooled 관계를 해석할 때 편중을 확인한다.
- 소수점·단위 입력 오류 의심 5행이 Validation 평균과 변동성에 큰 영향을 주었다.
- 이 5행은 오류로 확정된 값이 아니다. 기본 분석에는 유지하고, 원자료 확인 전에는 민감도 분석에서만 명시적으로 제외한다.
- IQR 이상치 후보는 자동 삭제하지 않는다. 완전 중복의 추가 복제 5행만 Train/Validation 누수 방지를 위해 제거한다.

## 모델과 검증

- 기준 Model 2는 normalized dose, PR tone, dose×tone, Tool로 구성한다.
- 단일 분할 R²보다 30회 반복검증 분포와 unseen-Lot 검증을 우선해 안정성을 판단한다.
- 예측성능의 안정성과 dose 방향의 안정성을 별도 질문으로 보고한다.
- 전체 변수 추가는 단순 기준보다 일관된 Validation 개선을 보이지 않았다. Random Forest 등 복잡한 모델로 바로 이동하지 않는다.
- Holdout/B 데이터는 분석·모델·서사 선택이 고정되기 전까지 읽거나 평가하지 않는다.

## 보고 경계

- 현재 결과는 특정 교육용 합성 데이터셋과 공정창에서 얻었다.
- 실제 Photo recipe의 일반 법칙, 장비 원인, PR chemistry 메커니즘으로 확대해석하지 않는다.
- 공정적 설명은 검증할 가설로 표시하고, 최종 확인에는 입력 원자료, Tool 상태, 계측 calibration과 tone별 통제 DOE가 필요하다.
