"""12주차 직접 쓰기 앱: 배포할 수 있는 대시보드를 처음부터 씁니다.

쓰는 법
1. 칸마다 주석의 할 일을 읽고 '# 여기에 씁니다' 아래에 코드를 씁니다. 번호(# 1-3 등)는 강의 PDF 제목의 번호입니다.
2. 내 컴퓨터에서 python -m streamlit run app.py 로 확인하고, 다 쓰면 python 배포_전_점검.py 로 [고침]이 0인지 봅니다.
3. requirements.txt도 직접 채웁니다(1-4). 먼저 배포_예제/를 보지 않고 써 봅니다. 막히면 PDF의 같은 번호 쪽을 봅니다.
4. 개인 프로젝트: sales.csv를 출처가 분명한 공개 데이터로 바꾸고 질문, 위젯, 차트를 내 데이터에 맞춰 고칩니다.
   차트 3개 이상과 위젯에 따라 바뀌는 숫자·차트가 프로젝트 최소 요건입니다.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

COLORS = {"A": "#0072B2", "B": "#D55E00"}

st.set_page_config(page_title="지점 실적 탐색", layout="wide")

st.title("어느 지점의 실적이 더 좋은가")
st.caption(
    "출처: 수업용 가상 데이터(sales.csv) · "
    "2026년 1~12월 지점별 월 실적 · 금액 단위: 백만원"
)

# 1. 데이터 불러오기
HERE = Path(__file__).parent
CSV_PATH = HERE / "sales.csv"

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

if not CSV_PATH.exists():
    st.error("sales.csv 파일을 찾을 수 없습니다.")
    st.stop()

data = load_data()

# 2. 사이드바 위젯
st.sidebar.header("분석 조건")

branches = st.sidebar.multiselect(
    "분석할 지점",
    options=["A", "B"],
    default=["A", "B"]
)

months = st.sidebar.slider(
    "분석할 월 범위",
    min_value=1,
    max_value=12,
    value=(1, 12)
)

metric_label = st.sidebar.selectbox(
    "표시할 지표",
    options=["매출", "영업이익"]
)

metric = "sales" if metric_label == "매출" else "profit"

# 3. 선택 조건에 따른 데이터 필터링
view = data[
    data["branch"].isin(branches)
    & data["month"].between(months[0], months[1])
].copy()

if view.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

# 4. 주요 지표 카드
total = view[metric].sum()
count = len(view)

col1, col2 = st.columns(2)

col1.metric(f"기간 {metric_label} 합계", f"{total:,.0f} 백만원")
col2.metric("표시 관측 수", f"{count}건")

st.divider()

# 5. 차트 1: 월별 실적 추이
st.subheader("월별 실적 추이")

monthly = (
    view.groupby(["month", "branch"], as_index=False)[metric]
    .sum()
)

fig1 = px.line(
    monthly,
    x="month",
    y=metric,
    color="branch",
    markers=True,
    color_discrete_map=COLORS,
    labels={
        "month": "월",
        metric: metric_label + " (백만원)",
        "branch": "지점"
    }
)

st.plotly_chart(fig1, use_container_width=True)

# 6. 차트 2, 3: 지점별 비교
left, middle = st.columns(2)

branch_total = (
    view.groupby("branch", as_index=False)[metric]
    .sum()
)

with left:
    st.subheader("지점별 기간 합계")

    fig2 = px.bar(
        branch_total,
        x="branch",
        y=metric,
        color="branch",
        color_discrete_map=COLORS,
        labels={
            "branch": "지점",
            metric: metric_label + " (백만원)"
        }
    )

    st.plotly_chart(fig2, use_container_width=True)

with middle:
    st.subheader("지점별 영업이익률")

    profit_total = (
        view.groupby("branch", as_index=False)
        [["sales", "profit"]]
        .sum()
    )

    profit_total["margin"] = (
        profit_total["profit"]
        / profit_total["sales"] * 100
    )

    fig3 = px.bar(
        profit_total,
        x="branch",
        y="margin",
        color="branch",
        color_discrete_map=COLORS,
        labels={
            "branch": "지점",
            "margin": "영업이익률 (%)"
        }
    )

    st.plotly_chart(fig3, use_container_width=True)

# 7. 상세 데이터 표
st.divider()
st.subheader("상세 매출 데이터")

st.dataframe(view, use_container_width=True)

# 8. CSV 다운로드
csv_data = view.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="분석 데이터 CSV 다운로드",
    data=csv_data,
    file_name="sales_analysis.csv",
    mime="text/csv"
)
