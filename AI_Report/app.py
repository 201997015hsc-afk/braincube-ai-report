import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from docx import Document
import io
import datetime
import os

# 1. 보안 및 페이지 설정
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
st.set_page_config(page_title="브레인큐브 AI 리포트", layout="wide")

# 2. 파일 경로 설정 (알려주신 주소 적용)
LOGO_PATH = "./AI_Report/braincube_logo.png"
BENCHMARK_PATH = "./AI_Report/benchmark.csv"

# 벤치마크 데이터 로드 및 계산
@st.cache_data
def load_benchmark_data(path):
    if os.path.exists(path):
        try:
            # 인코딩 문제 방지를 위해 utf-8과 cp949 둘 다 시도
            try:
                b_df = pd.read_csv(path, encoding='utf-8')
            except:
                b_df = pd.read_csv(path, encoding='cp949')
                
            b_df.columns = [c.strip() for c in b_df.columns]
            # 컬럼 매칭
            c_map = {'CPA': ['평균 CPA', 'CPA', '전환단가'], 'CTR': ['평균 CTR', 'CTR', '클릭률']}
            for target, cands in c_map.items():
                for c in cands:
                    if c in b_df.columns:
                        b_df.rename(columns={c: target}, inplace=True)
                        break
            return {
                'avg_cpa': pd.to_numeric(b_df['CPA'], errors='coerce').mean(),
                'avg_ctr': pd.to_numeric(b_df['CTR'], errors='coerce').mean()
            }
        except: return None
    return None

benchmark_stats = load_benchmark_data(BENCHMARK_PATH)

# --- 화면 레이아웃 ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=300) 
    else:
        st.markdown("<h1 style='text-align: center; color: orange;'>BRAINCUBE</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AI 캠페인 분석 솔루션</h2>", unsafe_allow_html=True)
    st.write("---")

# --- 메인 분석 로직 ---
uploaded_file = st.file_uploader("📊 광고주 캠페인 리포트를 업로드하세요", type=["csv", "xlsx"])

if uploaded_file:
    # 데이터 로드
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    # 컬럼 매칭
    col_map = {'소진액': ['소진액', '광고비', 'Spend'], 'CTR': ['CTR', '클릭률'], 'CPA': ['CPA', '전환단가'], '전환수': ['전환수', '전환'], '매체': ['매체', '매체명']}
    for target, candidates in col_map.items():
        for cand in candidates:
            if cand in df.columns:
                df.rename(columns={cand: target}, inplace=True)
                break
    
    # 수치 변환
    for c in ['소진액', 'CTR', 'CPA', '전환수']:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    st.success("✅ 캠페인 데이터 분석 완료!")

    # 탭 구성
    t1, t2, t3 = st.tabs(["📈 핵심 성과", "🎨 소재 효율", "🤖 AI 리포트"])
    
    with t1:
        st.subheader("종합 퍼포먼스 (vs 26년 평균)")
        m1, m2, m3, m4 = st.columns(4)
        curr_ctr, curr_cpa = df['CTR'].mean(), df['CPA'].mean()
        
        # 벤치마크와 비교 (Delta 계산)
        ctr_delta = f"{((curr_ctr - benchmark_stats['avg_ctr'])/benchmark_stats['avg_ctr']*100):.1f}%" if benchmark_stats else None
        cpa_delta = f"{((curr_cpa - benchmark_stats['avg_cpa'])/benchmark_stats['avg_cpa']*100):.1f}%" if benchmark_stats else None

        m1.metric("총 소진액", f"{df['소진액'].sum():,.0f}원")
        m2.metric("평균 CTR", f"{curr_ctr:.2f}%", delta=ctr_delta)
        m3.metric("평균 CPA", f"{curr_cpa:,.0f}원", delta=cpa_delta, delta_color="inverse")
        m4.metric("총 전환수", f"{df['전환수'].sum():,.0f}건")

        if '매체' in df.columns:
            st.plotly_chart(px.bar(df, x='매체', y='소진액', color='CPA', title="매체별 현황 (색상: CPA)", color_continuous_scale="Oranges"), width='stretch')

    with t3:
        st.subheader("브레인큐브 AI 전략 제안")
        if st.button("AI 리포트 생성 시작"):
            with st.spinner("데이터를 기반으로 최적의 전략을 수립 중입니다..."):
                summary = df.groupby('매체').agg({'소진액':'sum', 'CPA':'mean', '전환수':'sum'}).to_string()
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"광고 대행사 마케터로서 분석해줘: {summary}")
                st.markdown(res.text)
                
                # 다운로드 기능
                doc = Document()
                doc.add_heading('AI 캠페인 분석 리포트', 0)
                doc.add_paragraph(res.text)
                bio = io.BytesIO()
                doc.save(bio)
                st.download_button("📄 리포트 다운로드(.docx)", bio.getvalue(), f"Report_{datetime.date.today()}.docx")

else:
    if not benchmark_stats:
        st.warning("⚠️ 26년 평균 데이터를 읽어오지 못했습니다. 파일이 AI_Report 폴더 안에 있는지 확인해주세요.")
    st.info("파일을 업로드하면 브레인큐브 26년 실적 데이터와 비교 분석을 시작합니다.")

st.markdown("---")
st.caption("© 2026 Braincube AI Marketing Solutions. All rights reserved.")
