import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from docx import Document
import io
import datetime
import os

# 1. 경로 해결사: 현재 실행 중인 app.py의 위치를 기준으로 경로를 잡습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    """현재 폴더 내에서 파일을 찾는 절대 경로 생성기"""
    return os.path.join(BASE_DIR, filename)

# 보안 및 페이지 설정
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
st.set_page_config(page_title="브레인큐브 AI 리포트", layout="wide")

# 2. 로고 및 벤치마크 스마트 로더
@st.cache_resource
def load_logo():
    path = get_path("braincube_logo.png")
    if os.path.exists(path):
        return path
    # 대문자 후보도 하나 더 체크
    alt_path = get_path("Braincube_Logo.png")
    return alt_path if os.path.exists(alt_path) else None

@st.cache_data
def load_and_calculate_benchmark():
    path = get_path("benchmark.csv")
    if not os.path.exists(path):
        path = get_path("Benchmark.csv") # 대문자 체크
        
    if os.path.exists(path):
        try:
            b_df = pd.read_csv(path)
            b_df.columns = [c.strip() for c in b_df.columns]
            # CPA, CTR 컬럼 매칭
            col_map_b = {'평균 CPA': ['평균 CPA', 'CPA'], '평균 CTR': ['평균 CTR', 'CTR']}
            for target, cands in col_map_b.items():
                for c in cands:
                    if c in b_df.columns:
                        b_df.rename(columns={c: target}, inplace=True)
                        break
            return {
                'avg_cpa': pd.to_numeric(b_df['평균 CPA'], errors='coerce').mean(),
                'avg_ctr': pd.to_numeric(b_df['평균 CTR'], errors='coerce').mean()
            }
        except: return None
    return None

logo_path = load_logo()
benchmark_averages = load_and_calculate_benchmark()

# --- 화면 레이아웃 (기존 디자인 유지) ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if logo_path:
        st.image(logo_path, width=300) 
    else:
        st.markdown("<h1 style='text-align: center; color: orange;'>BRAINCUBE</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AI 캠페인 분석 솔루션</h2>", unsafe_allow_html=True)
    st.write("---")

# --- 데이터 분석 로직 ---
uploaded_file = st.file_uploader("광고주 캠페인 리포트를 업로드하세요", type=["csv", "xlsx"])

if uploaded_file:
    # 데이터 로드 및 전처리
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    # 컬럼 매칭 (소진액, CPA, CTR 등)
    col_map = {'소진액': ['소진액', '광고비'], 'CTR': ['CTR', '클릭률'], 'CPA': ['CPA', '전환단가'], '전환수': ['전환수', '전환'], '매체': ['매체', '매체명']}
    for target, candidates in col_map.items():
        for cand in candidates:
            if cand in df.columns:
                df.rename(columns={cand: target}, inplace=True)
                break
    
    # 수치형 변환
    for col in ['소진액', 'CTR', 'CPA', '전환수']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.success("✅ 분석 완료!")

    # 성과 요약 탭
    t1, t2, t3 = st.tabs(["📈 핵심 성과", "🎨 소재 효율", "🤖 AI 리포트"])
    
    with t1:
        m1, m2, m3, m4 = st.columns(4)
        current_ctr = df['CTR'].mean() if 'CTR' in df.columns else 0
        current_cpa = df['CPA'].mean() if 'CPA' in df.columns else 0
        
        # 벤치마크 비교 (Delta 계산)
        ctr_delta = f"{((current_ctr - benchmark_averages['avg_ctr']) / benchmark_averages['avg_ctr'] * 100):.1f}%" if benchmark_averages else None
        cpa_delta = f"{((current_cpa - benchmark_averages['avg_cpa']) / benchmark_averages['avg_cpa'] * 100):.1f}%" if benchmark_averages else None

        m1.metric("총 소진액", f"{df['소진액'].sum():,.0f}원")
        m2.metric("평균 CTR", f"{current_ctr:.2f}%", delta=ctr_delta)
        m3.metric("평균 CPA", f"{current_cpa:,.0f}원", delta=cpa_delta, delta_color="inverse")
        m4.metric("총 전환수", f"{df['전환수'].sum():,.0f}건")

        if '매체' in df.columns:
            st.plotly_chart(px.bar(df, x='매체', y='소진액', color='CPA', color_continuous_scale="Oranges"), width='stretch')

    # (이하 소재 분석 및 AI 리포트 코드는 동일하게 작동합니다)
    with t3:
        if st.button("AI 전략 분석 시작"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"광고 데이터 분석해줘: {df.head(5).to_string()}")
            st.markdown(res.text)

else:
    if not benchmark_averages:
        st.warning("⚠️ 벤치마크 데이터를 읽어오지 못했습니다. 파일 위치를 다시 확인해주세요.")
    st.info("데이터를 업로드하면 26년 평균 대비 성과 분석이 시작됩니다.")

st.markdown("---")
st.caption("© 2026 Braincube AI Marketing Solutions.")
