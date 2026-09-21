# my-data-app
import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(page_title="어제 박스오피스 순위", layout="wide")

st.title("🎬 어제 박스오피스 순위")


# --- 1. 날짜 및 API 데이터 로드 함수 (캐시 적용) ---
# ttl=3600: 같은 날짜 데이터 요청 시 1시간(3600초) 동안 API를 다시 호출하지 않고 저장된 결과를 사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(target_date_str, api_key):
    """KOBIS API에서 어제 날짜의 박스오피스 데이터를 가져오는 함수"""
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date_str}

    try:
        # API 요청 보내기 (타임아웃 10초 설정)
        response = requests.get(url, params=params, timeout=10)
        # HTTP 상태 코드가 200이 아닌 경우 예외 발생
        response.raise_for_status()
        data = response.json()
        return data, None
    except requests.exceptions.RequestException as e:
        # 네트워크 오류 발생 시
        return None, f"네트워크 통신 중 오류가 발생했습니다: {e}"


# --- 2. secrets에서 인증키 불러오기 ---
# Streamlit Cloud의 Secrets 설정에 저장된 KOBIS_KEY를 읽어옵니다.
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "⚠️ 인증키가 설정되지 않았습니다.\n\n"
        "**확인 사항:**\n"
        "1. Streamlit Cloud의 App Settings > Secrets 메뉴로 이동하세요.\n"
        '2. `KOBIS_KEY = "발급받은_API_키"` 형태로 비밀키를 입력했는지 확인하세요.'
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]


# --- 3. 한국 시간(KST) 기준 어제 날짜 계산 ---
# 서버 시계가 해외(UTC 등) 기준이어도 항상 한국 시간 기준으로 '어제'를 계산합니다.
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst)
yesterday_kst = now_kst - datetime.timedelta(days=1)
target_dt_str = yesterday_kst.strftime("%Y%m%d")  # YYYYMMDD 형식
display_date_str = yesterday_kst.strftime("%Y년 %m월 %d일")

st.caption(f"📅 기준 일자: **{display_date_str}** (한국 시간 기준)")


# --- 4. API 데이터 불러오기 및 예외 처리 ---
data, error_msg = fetch_box_office_data(target_dt_str, api_key)

# 4-1. 요청 자체 실패 시
if error_msg:
    st.error(
        f"⚠️ 데이터를 불러오지 못했습니다.\n\n"
        f"**오류 내용:** {error_msg}\n\n"
        "**확인 사항:** 인터넷 연결 상태를 확인해 주세요."
    )
    st.stop()

# 4-2. API 응답 중 faultInfo(인증키 오류 등)가 포함되어 온 경우
if "faultInfo" in data:
    fault_message = data["faultInfo"].get("message", "알 수 없는 오류")
    st.error(
        f"⚠️ API 요청 오류가 발생했습니다.\n\n"
        f"**오류 메시지:** {fault_message}\n\n"
        "**확인 사항:**\n"
        "1. Streamlit Secrets에 입력한 `KOBIS_KEY` 값이 정확한지 확인해 주세요.\n"
        "2. 영화진흥위원회(KOBIS) 개발자 센터에서 키가 정상 발급/활성화되었는지 확인해 주세요."
    )
    st.stop()

# 4-3. 응답에 boxOfficeResult가 없거나 dailyBoxOfficeList 목록이 비어있는 경우
box_office_result = data.get("boxOfficeResult", {})
movie_list = box_office_result.get("dailyBoxOfficeList", [])

if not movie_list:
    st.warning(
        "⚠️ 해당 날짜의 박스오피스 데이터가 비어 있습니다.\n\n"
        "**확인 사항:**\n"
        "1. 아직 해당 일자의 데이터가 집계되지 않았을 수 있습니다.\n"
        "2. 영화진흥위원회 API 서비스 점검 시간인지 확인해 주세요."
    )
    st.stop()


# --- 5. 데이터 가공 (문자열 -> 숫자 변환) ---
df = pd.DataFrame(movie_list)

# 필요한 컬럼만 선택
df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
    ]
]

# 문자열로 들어온 숫자 데이터들을 숫자 타입(int)으로 변환
df["rank"] = pd.to_numeric(df["rank"])
df["audiCnt"] = pd.to_numeric(df["audiCnt"])
df["audiAcc"] = pd.to_numeric(df["audiAcc"])
df["scrnCnt"] = pd.to_numeric(df["scrnCnt"])

# 순위 기준으로 오름차순 정렬
df = df.sort_values(by="rank", ascending=True)


# --- 6. 1위 영화 지표 카드 (st.metric) ---
top_1 = df.iloc[0]

st.subheader(f"🥇 1위: {top_1['movieNm']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="일별 관객수", value=f"{top_1['audiCnt']:,} 명")
with col2:
    st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
with col3:
    st.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")

st.markdown("---")


# --- 7. 관객수 상위 5편 막대그래프 ---
st.subheader("📊 관객수 상위 5개 영화")

# 상위 5개 추출
df_top5 = df.head(5).copy()

# 막대그래프용 데이터프레임 정리 (영화명을 인덱스로 설정)
chart_data = df_top5.set_index("movieNm")[["audiCnt"]]
chart_data.columns = ["일별 관객수"]

st.bar_chart(chart_data)

st.markdown("---")


# --- 8. 전체 박스오피스 표 출력 ---
st.subheader("📋 박스오피스 전체 순위")

# 화면 표시용 컬럼명 변경 및 숫자에 쉼표(,) 서식 적용
display_df = df.copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수",
]

# 숫자를 읽기 좋게 1,000 단위 쉼표 형태로 포맷팅
display_df["관객수"] = display_df["관객수"].apply(lambda x: f"{x:,}")
display_df["누적관객"] = display_df["누적관객"].apply(lambda x: f"{x:,}")
display_df["스크린수"] = display_df["스크린수"].apply(lambda x: f"{x:,}")

# 인덱스 숨기고 테이블 출력
st.dataframe(display_df, use_container_width=True, hide_index=True)
