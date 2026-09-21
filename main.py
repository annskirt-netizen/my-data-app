import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide",
)

# 앱 제목
st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.caption("1년치(365일) 박스오피스 데이터를 바탕으로 시간에 따른 영화 데이터의 변화를 탐색합니다.")


# --- 1. 데이터 로드 및 전처리 (캐시 적용) ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"
    # CSV 데이터 로드
    df = pd.read_csv(url)

    # 날짜 열을 문자열로 변환 후 datetime 객체로 변환 (예: 20230101 -> 2023-01-01)
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str), format="%Y%m%d")

    # 숫자 데이터 정형화
    df["순위"] = pd.to_numeric(df["순위"])
    df["일관객"] = pd.to_numeric(df["일관객"])
    df["누적관객"] = pd.to_numeric(df["누적관객"])
    df["스크린수"] = pd.to_numeric(df["스크린수"])
    df["상영횟수"] = pd.to_numeric(df["상영횟수"])

    return df


# 데이터 불러오기
try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# --- 2. [구역 1] 개별 영화의 날짜별 일관객 변화 ---
st.subheader("📌 구역 1. 개별 영화의 날짜별 일관객 추이")

# 전체 영화 목록 추출 (가나다순 정렬)
movie_list = sorted(df["영화명"].dropna().unique())

# 영화 선택 드롭다운
selected_movie = st.selectbox(
    "📊 관객수 추이를 확인할 영화를 선택하세요:",
    movie_list,
    index=0,
)

# 선택된 영화 데이터 필터링 (날짜순 정렬)
movie_df = df[df["영화명"] == selected_movie].sort_values("날짜")

if not movie_df.empty:
    # Plotly 선 그래프 생성
    fig1 = px.line(
        movie_df,
        x="날짜",
        y="일관객",
        title=f"'{selected_movie}' 날짜별 일관객 변화",
        labels={"날짜": "조회 날짜", "일관객": "일일 관객수 (명)"},
        markers=True,
    )

    # 마우스 호버(Hover) 툴팁 및 레이아웃 설정
    fig1.update_traces(
        hovertemplate="<b>날짜:</b> %{x|%Y-%m-%d}<br><b>일관객:</b> %{y:,}명<extra></extra>"
    )
    fig1.update_layout(
        xaxis_title="날짜",
        yaxis_title="일관객수 (명)",
        hovermode="x unified",
    )

    # 그래프 출력
    st.plotly_chart(fig1, use_container_width=True)

    # 그래프 설명 문구
    st.info(
        f"💡 **이 그래프로 알 수 있는 것:** "
        f"'{selected_movie}'의 개봉 초기 관객 집중도와 주말/평일 간 관객수 변동 패턴, 흥행 유지 기간을 한눈에 파악할 수 있습니다."
    )
else:
    st.warning("선택한 영화의 데이터가 없습니다.")

st.markdown("---")


# --- 3. [구역 2] 일관객 합계 상위 5개 영화의 날짜별 추이 비교 ---
st.subheader("📌 구역 2. 관객수 TOP 5 영화의 일관객 추이 비교")

# 1. 기간 내 일관객 합계 상위 5개 영화 추출
top5_movies = (
    df.groupby("영화명")["일관객"]
    .sum()
    .nlargest(5)
    .index.tolist()
)

# 2. 상위 5개 영화 데이터만 필터링
df_top5 = df[df["영화명"].isin(top5_movies)].sort_values("날짜")

# 3. Plotly 선 그래프 생성 (color='영화명'으로 영화별 색상 구분)
fig2 = px.line(
    df_top5,
    x="날짜",
    y="일관객",
    color="영화명",
    title="기간 내 관객수 TOP 5 영화의 날짜별 일관객 변화 비교",
    labels={"날짜": "조회 날짜", "일관객": "일일 관객수 (명)", "영화명": "영화 제목"},
)

# 툴팁 및 레이아웃 설정
fig2.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>"
)
fig2.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객수 (명)",
    legend_title_text="영화 (클릭하여 켜기/끄기)",
    hovermode="x unified",
)

# 그래프 출력
st.plotly_chart(fig2, use_container_width=True)

# 그래프 설명 문구
top5_str = ", ".join(top5_movies)
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** "
    f"기간 내 흥행 TOP 5 영화({top5_str})의 전성기 시점과 일일 최다 관객수, 흥행이 지속된 기간을 상호 비교할 수 있으며 범례를 클릭해 특정 영화만 따로 분석할 수 있습니다."
)
