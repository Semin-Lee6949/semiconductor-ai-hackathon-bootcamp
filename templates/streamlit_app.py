"""수강생용 재현 앱 골격.

정답 모델이 아니라 새 CSV에서도 데이터 품질과 탐색 그래프를 다시 만드는
최소 시작점이다. 프로젝트 질문에 맞게 TODO를 직접 수정한다.
"""

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Semiconductor AI Project", layout="wide")
st.title("반도체 데이터 재현 실험실")
st.caption("교육용·공개 데이터만 사용합니다. 실제 회사 데이터와 내부 Spec은 올리지 않습니다.")

uploaded = st.file_uploader("새 CSV 불러오기", type="csv")
if uploaded is None:
    st.info("주제별 train.csv 또는 자신의 공개·교육용 CSV를 선택하세요.")
    st.stop()

data = pd.read_csv(uploaded)
if data.empty:
    st.error("행이 없는 CSV입니다. 다른 파일을 선택하세요.")
    st.stop()

st.subheader("1. 데이터 탐색")
c1, c2, c3 = st.columns(3)
c1.metric("행", f"{len(data):,}")
c2.metric("열", f"{data.shape[1]:,}")
c3.metric("결측", f"{int(data.isna().sum().sum()):,}")
st.dataframe(data.head(30), use_container_width=True)

numeric = data.select_dtypes(include="number").columns.tolist()
if not numeric:
    st.warning("수치형 열이 없습니다. 데이터 사전과 데이터 타입을 확인하세요.")
    st.stop()

st.subheader("2. 탐색 그래프")
x = st.selectbox("X 변수", numeric)
y_candidates = [column for column in numeric if column != x]
if y_candidates:
    y = st.selectbox("Y 변수", y_candidates)
    st.scatter_chart(data[[x, y]].dropna(), x=x, y=y)
else:
    st.bar_chart(data[x].dropna().value_counts().sort_index())

st.subheader("3. 프로젝트 TODO")
st.markdown(
    """
    - 문제와 사용자 결정을 한 문장으로 표시한다.
    - 스키마·단위·결측·중복·이상점·편중 감사를 추가한다.
    - 단순 기준모델과 개선모델을 분리된 Holdout에서 비교한다.
    - 전공지식에 따른 대안 가설과 적용 불가 조건을 표시한다.
    - AI가 만든 부분과 사람이 검증·수정한 부분을 구분한다.
    """
)
