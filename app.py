import re
from html import escape
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="공사정보 관리",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXCEL_FILE = Path("매장리스트.xlsx")
DATA_FILE = Path("construction_records.csv")

REQUIRED_COLUMNS = ["마케팅팀", "대리점명", "매장코드", "매장명", "주소"]
PERIOD_PATTERN = r"^\d{4}-\d{2}-\d{2}\s~\s\d{4}-\d{2}-\d{2}$"


# =========================
# CSS 디자인
# =========================
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }

    .hero-card {
        padding: 24px 26px;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%);
        color: white;
        box-shadow: 0 16px 35px rgba(15, 23, 42, 0.18);
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 6px;
        letter-spacing: -0.6px;
    }

    .hero-sub {
        font-size: 15px;
        color: #cbd5e1;
        line-height: 1.5;
    }

    .info-card {
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        background-color: #ffffff;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 14px;
    }

    .metric-label {
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .metric-value {
        color: #0f172a;
        font-size: 17px;
        font-weight: 800;
        word-break: keep-all;
    }

    .small-help {
        color: #64748b;
        font-size: 13px;
        line-height: 1.45;
    }

    div[data-testid="stRadio"] > label {
        font-weight: 800;
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stTextInput"] label {
        font-weight: 700;
        color: #0f172a;
    }

    .stButton > button {
        border-radius: 12px;
        height: 42px;
        font-weight: 800;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero-card {
            padding: 20px;
            border-radius: 18px;
        }

        .hero-title {
            font-size: 24px;
        }

        .metric-value {
            font-size: 15px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# 데이터 로딩 함수
# =========================
@st.cache_data(show_spinner=False)
def load_store_data() -> pd.DataFrame:
    if not EXCEL_FILE.exists():
        st.error("매장리스트.xlsx 파일이 없습니다. app.py와 같은 폴더에 넣어 주세요.")
        st.stop()

    df = pd.read_excel(
        EXCEL_FILE,
        dtype={
            "매장코드": str,
            "대리점코드": str,
        },
    )

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_columns:
        st.error(f"엑셀에 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
        st.stop()

    df = df.copy()

    for col in REQUIRED_COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df = df[df["매장코드"] != ""]
    df = df.drop_duplicates(subset=["매장코드"], keep="first")

    return df


def load_records() -> pd.DataFrame:
    columns = [
        "등록일시",
        "마케팅팀",
        "대리점명",
        "매장명",
        "매장코드",
        "주소",
        "공사기간",
        "공사완료여부",
    ]

    if not DATA_FILE.exists():
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(DATA_FILE, dtype=str).fillna("")

    for col in columns:
        if col not in df.columns:
            df[col] = ""

    return df[columns]


def save_records(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def validate_period(period: str) -> tuple[bool, str]:
    period = period.strip()

    if not re.match(PERIOD_PATTERN, period):
        return False, "공사기간은 `2026-05-21 ~ 2026-06-21` 형식으로 입력해 주세요."

    start_text, end_text = [x.strip() for x in period.split("~")]

    try:
        start_date = datetime.strptime(start_text, "%Y-%m-%d")
        end_date = datetime.strptime(end_text, "%Y-%m-%d")
    except ValueError:
        return False, "존재하지 않는 날짜입니다. 날짜를 다시 확인해 주세요."

    if start_date > end_date:
        return False, "공사 시작일은 종료일보다 늦을 수 없습니다."

    return True, ""


def make_store_card(store: pd.Series) -> None:
    safe_store = {key: escape(str(value)) for key, value in store.items()}

    st.markdown('<div class="info-card">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.4, 1.1, 2.2])

    with col1:
        st.markdown('<div class="metric-label">매장명</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{safe_store["매장명"]}</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown('<div class="metric-label">매장코드</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{safe_store["매장코드"]}</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown('<div class="metric-label">주소</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{safe_store["주소"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# 데이터 준비
# =========================
stores = load_store_data()
records = load_records()


# =========================
# 상단 타이틀
# =========================
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">공사정보 관리 시스템</div>
        <div class="hero-sub">
            매장코드 직접 입력 또는 마케팅팀 → 대리점명 → 매장명 순서로 공사 매장을 선택하고,
            공사기간과 완료여부를 등록·조회·삭제할 수 있습니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# 사이드바
# =========================
with st.sidebar:
    st.subheader("📌 사용 안내")

    st.markdown(
        """
        <div class="small-help">
        1. 매장을 선택합니다.<br>
        2. 공사기간을 입력합니다.<br>
        3. 완료여부 Y/N을 선택합니다.<br>
        4. 등록된 공사정보는 하단에서 조회·삭제합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption(f"전체 매장 수: {len(stores):,}개")
    st.caption(f"등록 공사정보: {len(records):,}건")


# =========================
# 1. 공사매장 선택
# =========================
st.subheader("1. 공사매장 선택")

select_method = st.radio(
    "선택 방법",
    ["매장코드 직접 입력", "마케팅팀 → 대리점명 → 매장명 조회"],
    horizontal=True,
)

selected_store = None

if select_method == "매장코드 직접 입력":
    code = st.text_input(
        "매장코드",
        placeholder="예: D331250000",
        help="엑셀의 매장코드를 입력하면 매장 정보를 자동 조회합니다.",
    ).strip()

    if code:
        result = stores[stores["매장코드"].str.upper() == code.upper()]

        if result.empty:
            st.warning("입력한 매장코드와 일치하는 매장이 없습니다.")
        else:
            selected_store = result.iloc[0]

else:
    col1, col2, col3 = st.columns(3)

    with col1:
        marketing_options = sorted(stores["마케팅팀"].dropna().unique().tolist())
        selected_marketing = st.selectbox("마케팅팀", marketing_options)

    agency_df = stores[stores["마케팅팀"] == selected_marketing]

    with col2:
        agency_options = sorted(agency_df["대리점명"].dropna().unique().tolist())
        selected_agency = st.selectbox("대리점명", agency_options)

    store_df = agency_df[agency_df["대리점명"] == selected_agency].copy()
    store_df["매장표시명"] = store_df["매장명"] + " / " + store_df["매장코드"]

    with col3:
        store_options = store_df["매장표시명"].tolist()
        selected_store_label = st.selectbox("매장명", store_options)

    selected_code = selected_store_label.split(" / ")[-1]
    selected_store = store_df[store_df["매장코드"] == selected_code].iloc[0]


# =========================
# 2. 공사정보 입력
# =========================
if selected_store is not None:
    st.subheader("2. 선택 매장 정보 및 공사정보 입력")

    make_store_card(selected_store)

    input_col1, input_col2, input_col3 = st.columns([2.2, 1.1, 1.1])

    with input_col1:
        period = st.text_input(
            "공사기간",
            placeholder="2026-05-21 ~ 2026-06-21",
            help="YYYY-MM-DD ~ YYYY-MM-DD 형식으로 입력해 주세요.",
        )

    with input_col2:
        complete_yn = st.selectbox("공사완료여부", ["N", "Y"])

    with input_col3:
        st.write("")
        st.write("")
        save_button = st.button(
            "공사정보 등록",
            width="stretch",
            type="primary",
        )

    if save_button:
        is_valid, message = validate_period(period)

        if not is_valid:
            st.error(message)
        else:
            new_record = {
                "등록일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "마케팅팀": selected_store["마케팅팀"],
                "대리점명": selected_store["대리점명"],
                "매장명": selected_store["매장명"],
                "매장코드": selected_store["매장코드"],
                "주소": selected_store["주소"],
                "공사기간": period.strip(),
                "공사완료여부": complete_yn,
            }

            records = load_records()
            records = pd.concat(
                [records, pd.DataFrame([new_record])],
                ignore_index=True,
            )

            save_records(records)

            st.success("공사정보가 등록되었습니다.")
            st.rerun()


# =========================
# 3. 공사정보 조회 / 삭제
# =========================
st.divider()
st.subheader("3. 등록된 공사정보 조회 / 삭제")

records = load_records()

if records.empty:
    st.info("아직 등록된 공사정보가 없습니다.")

else:
    search_col1, search_col2, search_col3 = st.columns([1.2, 1.2, 1])

    with search_col1:
        keyword = st.text_input(
            "검색어",
            placeholder="매장명, 매장코드, 주소 검색",
        )

    with search_col2:
        status_filter = st.selectbox("완료여부 필터", ["전체", "Y", "N"])

    with search_col3:
        st.write("")
        st.write("")

        csv_data = records.to_csv(index=False, encoding="utf-8-sig")

        st.download_button(
            "CSV 다운로드",
            data=csv_data,
            file_name="construction_records.csv",
            mime="text/csv",
            width="stretch",
        )

    filtered = records.copy()

    if keyword:
        keyword_lower = keyword.lower()

        mask = (
            filtered["매장명"].str.lower().str.contains(keyword_lower, na=False)
            | filtered["매장코드"].str.lower().str.contains(keyword_lower, na=False)
            | filtered["주소"].str.lower().str.contains(keyword_lower, na=False)
            | filtered["대리점명"].str.lower().str.contains(keyword_lower, na=False)
            | filtered["마케팅팀"].str.lower().str.contains(keyword_lower, na=False)
        )

        filtered = filtered[mask]

    if status_filter != "전체":
        filtered = filtered[filtered["공사완료여부"] == status_filter]

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
        column_config={
            "등록일시": st.column_config.TextColumn("등록일시", width="medium"),
            "마케팅팀": st.column_config.TextColumn("마케팅팀", width="medium"),
            "대리점명": st.column_config.TextColumn("대리점명", width="medium"),
            "매장명": st.column_config.TextColumn("매장명", width="medium"),
            "매장코드": st.column_config.TextColumn("매장코드", width="medium"),
            "주소": st.column_config.TextColumn("주소", width="large"),
            "공사기간": st.column_config.TextColumn("공사기간", width="medium"),
            "공사완료여부": st.column_config.TextColumn("공사완료여부", width="small"),
        },
    )

    st.markdown("#### 삭제")

    delete_options = [
        f'{idx} | {row["매장명"]} | {row["매장코드"]} | {row["공사기간"]} | 완료:{row["공사완료여부"]}'
        for idx, row in records.iterrows()
    ]

    delete_target = st.selectbox("삭제할 공사정보 선택", delete_options)

    delete_col1, delete_col2 = st.columns([1, 3])

    with delete_col1:
        delete_button = st.button("선택 항목 삭제", width="stretch")

    if delete_button:
        delete_index = int(delete_target.split(" | ")[0])

        records = records.drop(index=delete_index).reset_index(drop=True)
        save_records(records)

        st.success("선택한 공사정보가 삭제되었습니다.")
        st.rerun()
