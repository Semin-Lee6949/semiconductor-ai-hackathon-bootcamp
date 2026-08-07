# 반도체 공정 AI 문제 10종

모든 변수·수치·Spec은 교육용 합성값입니다.

1. **Photo Dose–Focus Window:** CD·CDU·LER·결함을 함께 고려한 Margin Center
2. **Overlay 보정:** Translation·Rotation·Magnification과 Local Hot Spot 분리
3. **Dry Etch Endpoint:** OES·설비 시계열로 Endpoint·Over-etch·CD Bias 진단
4. **HAR Etch Profile:** Bowing·Taper·Microloading을 포함한 단면 SVG 시뮬레이션
5. **CMP 최적화:** Removal Rate·WIWNU·Dishing·Erosion의 Pareto Recipe
6. **증착 Run-to-Run APC:** Drift 감시와 다음 Run 보정량 제안
7. **설비 FDC:** 정상·Drift·Arc·Leak·Endpoint 이상과 점검 우선순위
8. **DRAM Cell Transistor:** Vth·Ion·Ioff·Retention Risk의 Monte Carlo 산포
9. **3D NAND Window:** P/E Cycle·Retention에 따른 Vth 분포·Read Window·오류 위험
10. **Virtual Lot:** Photo→Etch→CMP 변동 전파와 병목 공정

## A/B 데이터 원칙

- 같은 스키마와 화면 구조를 사용하되 주요 원인·교란변수·이상치·최적조건을 다르게 한다.
- A/B 모두 Holdout 데이터를 별도로 제공한다.
- 수강생이 같은 결론을 복사할 수 없도록 숨은 Interaction과 설비 편중을 달리한다.
- 정답은 모델명이 아니라 **발견해야 할 데이터 문제, 유효한 검증, 안전한 의사결정 범위**로 정의한다.
