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

st.markdown("---")


# --- 4. [구역 3] 날짜별 10위권 일관객 총합 영역 그래프 ---
st.subheader("📌 구역 3. 전체 박스오피스(10위권) 일일 총 관객수 추이")

# 1. 날짜별 일관객 합계 구하기
daily_total = (
    df.groupby("날짜")["일관객"]
    .sum()
    .reset_index()
    .sort_values("날짜")
)

# 2. 합계가 가장 컸던 상위 3일 추출
top3_days = daily_total.nlargest(3, "일관객")

# 3. Plotly 영역 그래프(Area Chart) 생성
fig3 = px.area(
    daily_total,
    x="날짜",
    y="일관객",
    title="날짜별 TOP 10 박스오피스 일일 총 관객수 변화",
    labels={"날짜": "조회 날짜", "일관객": "총 관객수 (명)"},
)

# 4. 상위 3일 위치에 주석(Annotation) 및 점 표시 추가
for rank, (_, row) in enumerate(top3_days.iterrows(), 1):
    date_str = row["날짜"].strftime("%Y-%m-%d")
    count_str = f"{int(row['일관객']):,}명"

    fig3.add_annotation(
        x=row["날짜"],
        y=row["일관객"],
        text=f"<b>[{rank}위] {date_str}</b><br>({count_str})",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#E74C3C",
        ax=0,
        ay=-45 - (rank * 10),
        bgcolor="#FFFFFF",
        bordercolor="#E74C3C",
        borderwidth=1,
        borderpad=4,
        font=dict(size=11, color="#2C3E50"),
    )

# 툴팁 및 레이아웃 설정
fig3.update_traces(
    hovertemplate="<b>날짜:</b> %{x|%Y-%m-%d}<br><b>총 관객수:</b> %{y:,}명<extra></extra>",
    line=dict(color="#3498DB"),
    fillcolor="rgba(52, 152, 219, 0.3)",
)
fig3.update_layout(
    xaxis_title="날짜",
    yaxis_title="총 관객수 (명)",
    hovermode="x unified",
)

# 그래프 출력
st.plotly_chart(fig3, use_container_width=True)

# 상위 3일 날짜 텍스트 구성
top3_text = ", ".join(
    [
        f"**{row['날짜'].strftime('%Y-%m-%d')}**({int(row['일관객']):,}명)"
        for _, row in top3_days.iterrows()
    ]
)

# 그래프 설명 문구
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** "
    f"1년간 극장가 전체의 성수기 및 연휴 대목(명절, 여름/겨울 방학 시즌)에 따른 관객 유입 규모 변화를 파악할 수 있으며, "
    f"가장 많은 관객이 극장을 찾은 상위 3일은 {top3_text} 입니다."
)

st.markdown("---")


# --- 5. [구역 4] 기간 내 총 관객수 TOP 10 가로 막대그래프 ---
st.subheader("📌 구역 4. 기간 내 누적 관객수 TOP 10 영화")

# 1. 영화별 총 관객수 및 10위권 집계 일수(날짜 수) 계산
top10_summary = (
    df.groupby("영화명")
    .agg(
        총관객수=("일관객", "sum"),
        차트인일수=("날짜", "nunique"),
    )
    .reset_index()
    .nlargest(10, "총관객수")
)

# 2. 관객수가 많은 영화가 그래프 상단에 오도록 내림차순 정렬
top10_summary = top10_summary.sort_values("총관객수", ascending=True)

# 3. Plotly 가로 막대그래프 생성
fig4 = px.bar(
    top10_summary,
    x="총관객수",
    y="영화명",
    orientation="h",
    text_auto=",",
    custom_data=["차트인일수"],
    title="1년간 박스오피스 총 관객수 TOP 10 영화",
    labels={"총관객수": "기간 내 총 관객수 (명)", "영화명": "영화 제목"},
)

# 4. 툴팁(Hover) 설정
fig4.update_traces(
    hovertemplate="<b>영화명:</b> %{y}<br><b>총 관객수:</b> %{x:,}명<br><b>10위권 진입 일수:</b> %{customdata[0]}일<extra></extra>",
    marker_color="#2ECC71",
)

fig4.update_layout(
    xaxis_title="총 관객수 (명)",
    yaxis_title="영화 제목",
)

# 그래프 출력
st.plotly_chart(fig4, use_container_width=True)

# 최고 흥행작 정보 추출
top_movie_name = top10_summary.iloc[-1]["영화명"]
top_movie_cnt = top10_summary.iloc[-1]["총관객수"]
top_movie_days = top10_summary.iloc[-1]["차트인일수"]

# 그래프 설명 문구
st.info(
    f"💡 **이 그래프로 알 수 있는 것:** "
    f"1년간 가장 많은 관객을 모은 흥행 TOP 10 영화의 관객 규모와 롱런 여부(10위권 유지 일수)를 비교할 수 있습니다. "
    f"1위는 **{top_movie_name}**({int(top_movie_cnt):,}명, {top_movie_days}일간 차트인)입니다."
)

st.markdown("---")


# --- 6. [구역 5] 월×요일별 일관객 합계 히트맵 ---
st.subheader("📌 구역 5. 월별·요일별 관객수 집계 (히트맵)")

# 1. 월과 요일 정보 추출
df_heatmap = df.copy()
df_heatmap["월"] = df_heatmap["날짜"].dt.strftime("%m월")

# 요일 한글 이름 매핑 (월요일 ~ 일요일)
day_map = {0: "월요일", 1: "화요일", 2: "수요일", 3: "목요일", 4: "금요일", 5: "토요일", 6: "일요일"}
df_heatmap["요일"] = df_heatmap["날짜"].dt.dayofweek.map(day_map)

# 2. 월 x 요일별 관객수 합계 피벗 테이블 생성
pivot_df = (
    df_heatmap.groupby(["월", "요일"])["일관객"]
    .sum()
    .reset_index()
)

# 요일 정렬 순서 지정 (월요일 ~ 일요일)
days_order = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

# Plotly 히트맵 생성
fig5 = px.density_heatmap(
    pivot_df,
    x="요일",
    y="월",
    z="일관객",
    category_orders={"요일": days_order},  # 월요일부터 일요일 순서로 고정
    color_continuous_scale="Viridis",  # 관객수가 많을수록 밝고 진한 색상
    title="월별·요일별 박스오피스 관객수 합계 히트맵",
    labels={"요일": "요일", "월": "월", "일관객": "총 관객수 (명)"},
    text_auto=False,
)

# 툴팁(Hover) 및 레이아웃 설정
fig5.update_traces(
    hovertemplate="<b>%{y} %{x}</b><br>총 관객수: %{z:,}명<extra></extra>"
)
fig5.update_layout(
    xaxis_title="요일",
    yaxis_title="월",
    coloraxis_colorbar=dict(title="관객수 (명)"),
)

# 그래프 출력
st.plotly_chart(fig5, use_container_width=True)

# 그래프 설명 문구
st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "1년 중 관객 유입이 가장 활발했던 특정 월의 주말(토/일) 패턴과, 평일 중 문화가 있는 날(수요일) 또는 신작 개봉일(수/목)의 시즌별 반응 차이를 직관적으로 확인할 수 있습니다."
)
