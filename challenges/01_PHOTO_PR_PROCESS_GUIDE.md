# Challenge 01 — PR Coat·Expose·Develop CD 문제해결

> 모든 변수와 수치는 교육용 합성값입니다. 특정 회사의 PR 재료, 노광기, 현상액, 공정조건 또는 실제 Recipe를 나타내지 않습니다.

## 1. 공정 흐름

```text
Coat → Soft Bake → Align/Focus → Exposure → PEB → Development → CD/CDU/LER/Defect 측정
```

이번 과제는 Dose–Focus만 최적화하지 않습니다. 코팅 두께와 열처리·현상 조건이 PR tone과 결합해 최종 retained resist line의 CD와 결함에 미치는 영향을 찾습니다.

## 2. Positive·Negative PR의 기본 차이

| 구분 | Positive PR | Negative PR |
|---|---|---|
| 노광부의 변화 | 현상액에 더 잘 녹는 방향 | 가교·불용화되는 방향 |
| 현상 후 제거되는 부분 | 노광부 | 비노광부 |
| 본 데이터의 retained line | 비노광 영역에서 남은 line | 노광 영역에서 남은 line |
| 교육용 주요 위험 | Under-dose·짧은 현상과 Scum, 과현상에 의한 line loss | 불충분한 노광·PEB의 crosslink margin, 과도한 widening |

PR의 실제 성능은 재료계, 파장, mask/feature tone, 광학계, PEB, developer에 따라 달라집니다. 표는 원리와 이 합성 데이터의 문제구조를 설명할 뿐 보편적 Recipe 규칙이 아닙니다.

## 3. 입력과 출력

### 입력

- `pr_tone`: `POSITIVE` 또는 `NEGATIVE`
- `retained_pattern_source`: 남은 line이 `EXPOSED` 또는 `UNEXPOSED` 영역인지 명시
- `exposure_dose_mj_cm2`, `normalized_dose_pct`
- `focus_um`
- `coat_thickness_nm`
- `softbake_temp_c`, `peb_temp_c`
- `develop_time_s`, `developer_concentration_pct`
- `field_x`, `field_y`, `tool_id`, `lot_id`, `sequence`

### 출력

- `resist_line_cd_nm`
- `cdu_3sigma_nm`
- `ler_nm`
- `scum_probability`
- `pattern_collapse_probability`
- `defect_probability`
- `spec_pass`

## 4. 꼭 발견해야 할 문제

### 문제 A — PR tone을 합치면 Dose–CD 관계가 사라질 수 있다

이 데이터는 retained resist line을 기준으로 Positive와 Negative의 Dose 반응 방향을 다르게 설계했습니다. 두 tone을 섞은 전체 상관계수만 계산하면 관계가 약해지거나 잘못 보일 수 있습니다.

확인 그래프:

```python
sns.lmplot(
    data=data,
    x="normalized_dose_pct",
    y="resist_line_cd_nm",
    hue="pr_tone",
    col="pr_tone",
)
```

### 문제 B — 코팅 두께는 단독효과가 아니다

두꺼운 PR은 Dose·PEB·현상조건과 결합해 CD, CDU, Scum, Collapse 위험을 바꿀 수 있습니다. `coat_thickness_nm`의 단일 회귀계수만으로 결론을 내리지 않습니다.

확인:

- 두께 구간별 Dose–CD 그래프
- 두께×PEB 2D heatmap
- PR tone별 Facet
- Tool·Field 위치별 재검증

### 문제 C — 이상점이 단위 오류인지 실제 조건인지 구분해야 한다

합성 학습 데이터에는 PEB 온도 혼합단위 오류와 수치 극단값이 들어 있습니다.

순서:

1. 물리적으로 의심되는 범위를 플래그
2. `sample_id`, Tool, Lot, sequence 확인
3. 삭제 전후 모델과 결론 비교
4. 원본은 보존하고 수정 로그 기록

## 5. 문제해결 시나리오

### 시나리오 1 — CD 평균이 이동했다

확인 순서:

1. PR tone과 제품 mix가 바뀌었는가?
2. 코팅 두께 분포가 이동했는가?
3. Dose·Focus가 아니라 PEB·현상 시간이 함께 움직였는가?
4. 특정 Tool·Field 위치에 집중됐는가?
5. 같은 tone·두께 구간에서도 이동이 유지되는가?

### 시나리오 2 — Scum이 증가했다

- Positive PR의 low normalized dose·짧은 현상 구간 확인
- 두꺼운 막과 결합하는지 확인
- Negative PR의 불충분한 crosslink 신호와 구분
- Scum만 줄이다 CD loss·LER·Collapse가 악화되지 않는지 확인

### 시나리오 3 — Negative PR line이 넓어졌다

- normalized dose, PEB, 두께 상호작용 확인
- 전체 평균이 아닌 Negative PR 안에서 분석
- Field radial·Tool bias 대안가설 검토
- 단일 조건 변경이 아니라 작은 DOE 후보 제안

### 시나리오 4 — 얇은 CD에서 Collapse 위험이 증가했다

- `coat_thickness_nm / resist_line_cd_nm` aspect proxy
- 현상시간과 PR tone 비교
- 결측·극단점 처리 전후 위험도 비교
- 실제 적용 전 기계적 물성·건조조건 추가 측정 제안

## 6. 최소 MVP 화면

1. PR tone 선택
2. 코팅 두께·Dose·Focus·PEB·현상시간 Slider
3. 예상 CD·CDU·LER
4. Scum·Collapse·전체 Defect 위험
5. 현재 조건과 후보 조건 전후 비교
6. 추천이 아니라 **추가 확인할 변수와 작은 DOE 후보**

전용 실습 그래프 생성:

```bash
python lessons/photo_pr_visualization_demo.py
```

결과는 `artifacts/photo_pr/photo_pr_process_gallery.png`에 저장됩니다.

## 7. 안전한 결론 예시

```text
교육용 합성 데이터에서는 retained resist line의 Dose–CD 반응이
PR tone에 따라 다른 방향으로 나타났으며, 코팅 두께와 PEB·현상시간의
상호작용이 일부 구간의 Scum 및 Collapse 위험과 함께 관찰됐다.
실제 공정 적용 전에는 PR 재료계, mask/feature tone, 광학 조건,
developer와 계측 재현성을 포함한 별도 DOE가 필요하다.
```

## 참고

- [Samsung Semiconductor — Photolithography: coating, exposure, development](https://semiconductor.samsung.com/support/tools-resources/fabrication-process/eight-essential-semiconductor-fabrication-processes-part-4-photolithography-laying-the-blueprint/)
- [EPFL CMi — Introduction to Photolithography](https://www.epfl.ch/research/facilities/cmi/process/photolithography/introductiontophotolithography/)
- [BYU Cleanroom — Lithography Definitions](https://www.cleanroom.byu.edu/node/208)
