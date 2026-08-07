# 1강 핵심 실습 — 숫자를 믿기 전에 데이터부터 의심하라

## 이 세션의 질문

> 수율 평균이 내려갔다. 공정이 변한 것인가, 측정·수집·표본 구성이 변한 것인가?

엔지니어는 모델 버튼을 누르기 전에 이 둘을 구분해야 합니다. 결측과 이상치는 귀찮아서 지우는 행이 아니라 **공정·설비·측정 시스템이 남긴 사건 기록**일 수 있습니다.

## 1. 왜 데이터 품질이 중요한가

### 결측값이 평균과 관계를 바꾼다

예를 들어 고온·고압 조건에서만 센서가 포화되어 값이 빠진다면, 결측행을 삭제한 데이터에는 위험조건이 체계적으로 적게 남습니다. 모델 성능이 좋아 보여도 실제 위험구간을 배우지 못합니다.

결측은 편의상 다음처럼 생각할 수 있습니다.

- **무작위 결측에 가까움:** 특정 조건과 관계없이 통신 패킷 일부가 유실
- **관측값과 관련된 결측:** 특정 Tool·Recipe·교대조에서 기록 누락이 증가
- **결측될 값 자체와 관련:** 센서 상한을 넘는 순간 측정이 비어 버림

이 구분은 데이터만 보고 확정할 수 없습니다. 발생 시점, Tool, 유지보수 이력, 센서 범위와 함께 확인해야 합니다.

### 이상치는 오류일 수도 있고 가장 중요한 신호일 수도 있다

- 소수점·단위 변환 오류
- 센서 고장이나 캘리브레이션 문제
- 중복 수집과 타임스탬프 어긋남
- 실제 Arc·Leak·Endpoint 실패
- 새로운 공정 Window 또는 희귀 불량

따라서 `IQR 밖 = 삭제`는 처리 규칙이 아니라 **검토 후보를 만드는 규칙**입니다.

### 잘못된 처리는 평가 누출을 만든다

전체 데이터의 평균·중앙값을 먼저 계산해 결측치를 채운 뒤 Train/Holdout을 나누면 Holdout 정보가 학습에 들어갑니다. 전처리 규칙은 Train에서 결정하고 Holdout에는 그대로 적용해야 합니다.

## 2. 데이터 처리의 안전한 순서

1. 원본을 읽기 전용으로 보존한다.
2. 스키마·단위·행 수를 확인한다.
3. 결측·중복·범위·극단값을 **열별 숫자**로 보고한다.
4. Tool·Lot·시간 구간별로 발생 위치를 본다.
5. 물리 한계와 측정 시스템을 확인한다.
6. 삭제·대체·변환 후보를 각각 비교한다.
7. 처리 전후 결론과 Holdout 성능을 비교한다.
8. 처리 이유와 영향을 로그로 남긴다.

## 3. 결측값 처리 선택지

| 상황 | 우선 검토 | 피할 행동 |
|---|---|---|
| ID·시간·Tool 같은 핵심 키 결측 | 원천 추적, 행 격리 | 임의 값 생성 |
| 입력 특성의 소량 결측 | 그룹·시간 패턴 확인, 중앙값/모델 대체 비교 | 전체 평균으로 무조건 대체 |
| 특정 Tool에 집중된 결측 | Tool 상태·센서 범위 확인, 결측 표시변수 | Tool 정보를 지우고 합치기 |
| 목표변수 결측 | 학습 제외 여부와 원천 재측정 검토 | 입력 특성처럼 임의 대체 |
| 연속 시계열의 짧은 공백 | 시간 간격과 공정 전환을 확인한 보간 | 긴 정지구간을 직선 연결 |

핵심은 “어떤 기법이 최고인가”가 아니라 **그 기법이 공정 의미를 왜곡하지 않는가**입니다.

## 4. 이상치 처리 선택지

1. **물리·단위 검사:** 온도, 압력, 유량, 속도 등의 가능한 범위 확인
2. **그룹 검사:** 전체 기준이 아니라 Tool·Recipe·제품군 안에서 비교
3. **시간 검사:** 단발 Spike인지 지속 Drift인지 확인
4. **강건 통계:** 평균과 표준편차뿐 아니라 중앙값·IQR·MAD 비교
5. **민감도 분석:** 원본, 플래그 추가, 제외, 제한 변환 결과를 함께 비교

삭제가 필요한 경우에도 원본은 수정하지 않고 제외 사유와 `sample_id`를 기록합니다.

## 5. 그래프는 질문에 따라 고른다

### 1개 수치변수의 분포

- Histogram: 분포 형태, 다봉성, 긴 꼬리
- KDE: 부드러운 밀도 비교. 표본이 적을 때 과해석 주의
- ECDF: 임계값 이하·이상의 비율을 직접 읽기 좋음

### 범주별 수치 비교

- Boxplot: 중앙값·IQR·이상치 후보
- Violin: 분포 모양. 표본 수를 함께 표시
- Strip/Swarm: 실제 관측값과 표본 수

Boxplot 하나만 보면 표본 수와 다봉성이 숨을 수 있으므로 실제 점을 겹쳐 봅니다.

### 두 수치변수의 관계

- Scatter: 비선형·이분산·군집·극단점
- Regression plot: 추세 보조선. 인과관계 증거가 아님
- Hexbin/2D density: 점이 너무 많아 겹칠 때

### 시간·Run 순서

- Line plot: Drift, Step change, 유지보수 전후
- Rolling median/quantile band: 노이즈 속 장기 변화

시간순 데이터를 임의 셔플한 산점도만 보면 Drift가 사라집니다.

### 다변량·공정 위치

- Correlation heatmap: 탐색용. 상관이 원인이라는 뜻은 아님
- Pairplot: 소수 핵심 변수의 관계와 그룹 분리
- Facet: Tool·Lot·Recipe별 동일 그래프 비교
- Wafer/field map: 공간 Hot Spot과 Edge/Center 차이

## 6. ggplot2·seaborn 갤러리 보는 법

### 강사 화면 1 — seaborn Example Gallery

[seaborn Example Gallery](https://seaborn.pydata.org/examples/index.html)

다음 순서로 5개만 엽니다.

1. `histplot/displot` — 분포와 긴 꼬리
2. `boxplot + stripplot` — Tool별 분포와 실제 점
3. `scatterplot/relplot` — 공정 입력과 KPI 관계
4. `lineplot` — Run 순서 Drift
5. `heatmap` — 결측 위치 또는 상관행렬

질문은 항상 같습니다.

```text
이 그래프는 어떤 의사결정 질문에 답하는가?
무엇을 보여주고 무엇을 숨기는가?
색·크기·Facet에 어떤 변수를 넣어야 교란을 볼 수 있는가?
```

### 강사 화면 2 — ggplot2 Reference

[ggplot2 Reference Gallery](https://ggplot2.tidyverse.org/reference/index.html)

ggplot2는 `data + aes + geom + stat + scale + facet`의 층으로 읽습니다.

```r
ggplot(data, aes(x = down_force_psi, y = yield_proxy, colour = tool_id)) +
  geom_point(alpha = 0.5) +
  geom_smooth(se = FALSE) +
  facet_wrap(~ tool_id)
```

Python 실습에서도 같은 생각을 사용합니다.

```python
sns.relplot(
    data=data,
    x="down_force_psi",
    y="yield_proxy",
    hue="tool_id",
    col="tool_id",
)
```

이 과정에서는 R과 Python 문법을 모두 암기하지 않습니다. **질문→변수 역할→그래프 구조**가 같다는 점을 이해하고, 실습은 Python·seaborn 하나로 통일합니다.

## 7. 직접 실행

프로젝트 루트에서:

```bash
python -m pip install -r requirements-class.txt
python lessons/data_quality_visualization_demo.py
```

Windows에서 `python` 대신 `py`가 필요한 경우:

```powershell
py -m pip install -r requirements-class.txt
py lessons/data_quality_visualization_demo.py
```

생성 결과:

- `artifacts/data_quality/cmp_audit_summary.json`
- `artifacts/data_quality/cmp_audit_gallery.png`

## 8. 그래프를 보고 답할 여섯 질문

1. 결측은 어떤 열·Tool·시간에 몰려 있는가?
2. 이상치 후보는 단위 오류인가, 실제 특이 공정인가?
3. 전체 관계가 Tool별로도 같은가?
4. 시간에 따라 기준선이 움직이는가?
5. 데이터 처리 전후 결론이 바뀌는가?
6. 이 결과로 사용자가 무엇을 결정하며, 추가로 무엇을 측정해야 하는가?

## 9. 강의 연결 문장

강사는 각 구간을 다음 문장으로 연결합니다.

1. **문제→설치:** “오늘은 평균을 계산하는 사람이 아니라 평균이 믿을 만한지 확인하는 엔지니어가 됩니다.”
2. **설치→감사:** “도구가 준비됐으니 모델보다 먼저 데이터가 어떤 방식으로 거짓말할 수 있는지 확인하겠습니다.”
3. **감사→그래프:** “숫자 표만으로 발생 위치가 보이지 않으므로 질문에 맞는 그래프로 바꾸겠습니다.”
4. **갤러리→실습:** “그래프를 고른 이유를 말할 수 있어야 합니다. 이제 같은 질문을 실제 CMP 데이터에 적용합니다.”
5. **그래프→Codex:** “AI에게 예쁜 차트를 요구하지 말고, 검증할 질문과 성공 기준을 먼저 줍니다.”
6. **Codex→프로젝트:** “도구 실습을 끝냈으니, 이제 내 직무에서 어떤 결정을 지원할지 주제를 좁힙니다.”
