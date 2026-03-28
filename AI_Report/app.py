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

# 파일 추적 엔진 (기존 유지)
def get_absolute_path(filename):
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.lower() == filename.lower():
                return os.path.join(root, f)
    return None

final_logo_path = get_absolute_path("braincube_logo.png")
final_benchmark_path = get_absolute_path("benchmark.csv")

# 벤치마크 데이터 로드
@st.cache_data
def load_benchmark_safe(path):
    if not path: return None
    for enc in ['utf-8', 'cp949', 'euc-kr']:
        try:
            b_df = pd.read_csv(path, encoding=enc)
            b_df.columns = [c.strip() for c in b_df.columns]
            c_map = {'CPA': ['평균 CPA', 'CPA', '전환단가'], 'CTR': ['평균 CTR', 'CTR', '클릭률']}
            for target, cands in c_map.items():
                for c in cands:
                    if c in b_df.columns:
                        b_df.rename(columns={c: target}, inplace=True)
                        break
            return {'avg_cpa': pd.to_numeric(b_df['CPA'], errors='coerce').mean(),
                    'avg_ctr': pd.to_numeric(b_df['CTR'], errors='coerce').mean()}
        except: continue
    return None

benchmark_stats = load_benchmark_safe(final_benchmark_path)

# --- 상단 레이아웃 ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if final_logo_path: st.image(final_logo_path, width=300) 
    else: st.markdown("<h1 style='text-align: center; color: orange;'>BRAINCUBE</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AI 캠페인 분석 솔루션</h2>", unsafe_allow_html=True)
    st.write("---")

# --- 메인 분석 로직 ---
uploaded_file = st.file_uploader("📊 광고주 캠페인 리포트를 업로드하세요", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns] # 공백 제거
    
    # [방어 로직 1] 컬럼명 강제 매칭
    col_map = {
        '소진액': ['소진액', '광고비', 'Spend', 'Cost', '금액'],
        'CTR': ['CTR', '클릭률', '클릭율'],
        'CPA': ['CPA', '전환단가', '단가', 'Cost per Action'],
        '전환수': ['전환수', '전환', 'Conversions'],
        '매체': ['매체', '매체명', 'Media']
    }
    for target, candidates in col_map.items():
        for cand in candidates:
            if cand in df.columns:
                df.rename(columns={cand: target}, inplace=True)
                break

    # [방어 로직 2] 수치 데이터 강제 변환
    for c in ['소진액', 'CTR', 'CPA', '전환수']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        else:
            df[c] = 0 # 아예 없으면 0으로 채운 열을 만듦 (KeyError 방지)

    st.success("✅ 분석 완료!")

    t1, t2, t3 = st.tabs(["📈 핵심 성과", "🎨 소재 효율", "🤖 AI 리포트"])
    
    with t1:
        st.subheader("종합 퍼포먼스 (vs 26년 평균)")
        m1, m2, m3, m4 = st.columns(4)
        
        # [방어 로직 3] 에러 없이 값 가져오기 (.get 사용)
        curr_ctr = df['CTR'].mean() if 'CTR' in df.columns else 0
        curr_cpa = df['CPA'].mean() if 'CPA' in df.columns else 0
        
        # 벤치마크 Delta 계산
        ctr_delta, cpa_delta = None, None
        if benchmark_stats:
            if benchmark_stats['avg_ctr'] > 0:
                ctr_delta = f"{((curr_ctr - benchmark_stats['avg_ctr'])/benchmark_stats['avg_ctr']*100):.1f}%"
            if benchmark_stats['avg_cpa'] > 0:
                cpa_delta = f"{((curr_cpa - benchmark_stats['avg_cpa'])/benchmark_stats['avg_cpa']*100):.1f}%"

        m1.metric("총 소진액", f"{df['소진액'].sum():,.0f}원")
        m2.metric("평균 CTR", f"{curr_ctr:.2f}%", delta=ctr_delta)
        m3.metric("평균 CPA", f"{curr_cpa:,.0f}원", delta=cpa_delta, delta_color="inverse")
        m4.metric("총 전환수", f"{df['전환수'].sum():,.0f}건")

        if '매체' in df.columns and df['소진액'].sum() > 0:
            st.plotly_chart(px.bar(df, x='매체', y='소진액', color='CPA', color_continuous_scale="Oranges"), width='stretch')
        else:
            st.warning("📊 차트를 그릴 매체 데이터나 소진액 데이터가 부족합니다.")

    with t3:
        if st.button("AI 전략 리포트 생성"):
            with st.spinner("분석 중..."):
                summary = df.head(10).to_string()
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"마케터로서 분석해줘: {summary}")
                st.markdown(res.text)

else:
    # 📌 하단 상태창 (업로드된 파일의 실제 컬럼명을 보여줘서 사용자 디버깅 도움)
    st.info("광고주 리포트를 업로드하면 분석이 시작됩니다.")
    if not benchmark_stats:
        st.warning("⚠️ 벤치마크 데이터를 읽지 못했습니다. 파일명과 위치를 확인하세요.")

st.markdown("---")
st.caption("© 2026 Braincube AI Marketing Solutions.")
