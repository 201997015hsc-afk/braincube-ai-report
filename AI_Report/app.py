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

# 🔥 [핵심 업데이트] 어디에 있든 파일을 찾아내는 '지능형 로더'
def find_and_load_file(filename):
    """현재 폴더 및 모든 하위 폴더에서 파일을 찾아 경로를 반환"""
    # 1. 대소문자 무시하고 모든 파일 목록 가져오기
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.lower() == filename.lower():
                return os.path.join(root, f)
    return None

# 파일 찾기 실행
logo_path = find_and_load_file("braincube_logo.png")
benchmark_path = find_and_load_file("benchmark.csv")

# 벤치마크 데이터 계산
@st.cache_data
def get_benchmark_stats(path):
    if not path: return None
    try:
        # 한국어 엑셀 깨짐 방지를 위해 encoding 설정 추가
        try:
            b_df = pd.read_csv(path, encoding='utf-8')
        except:
            b_df = pd.read_csv(path, encoding='cp949')
            
        b_df.columns = [c.strip() for c in b_df.columns]
        # 컬럼명 유연하게 매칭
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

benchmark_stats = get_benchmark_stats(benchmark_path)

# 2. 로고 및 타이틀 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if logo_path:
        st.image(logo_path, width=300) 
    else:
        st.markdown("<h1 style='text-align: center; color: orange;'>BRAINCUBE</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AI 캠페인 분석 솔루션</h2>", unsafe_allow_html=True)
    st.write("---")

# 3. 메인 분석 로직
uploaded_file = st.file_uploader("캠페인 로우데이터를 업로드하세요", type=["csv", "xlsx"])

if uploaded_file:
    # 데이터 로드
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    # 엑셀 제목 스마트 매칭
    col_map = {'소진액': ['소진액', '광고비', 'Spend'], 'CTR': ['CTR', '클릭률'], 'CPA': ['CPA', '전환단가'], '전환수': ['전환수', '전환'], '매체': ['매체', '매체명']}
    for target, candidates in col_map.items():
        for cand in candidates:
            if cand in df.columns:
                df.rename(columns={cand: target}, inplace=True)
                break
    
    # 숫자 변환
    for c in ['소진액', 'CTR', 'CPA', '전환수']:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    st.success("✅ 분석 완료!")

    # 탭 구성
    t1, t2, t3 = st.tabs(["📊 성과 지표", "🎨 소재 분석", "🤖 AI 리포트"])
    
    with t1:
        m1, m2, m3, m4 = st.columns(4)
        curr_ctr, curr_cpa = df['CTR'].mean(), df['CPA'].mean()
        
        # 벤치마크와 비교 (데이터가 있을 때만)
        ctr_delta = f"{((curr_ctr - benchmark_stats['avg_ctr'])/benchmark_stats['avg_ctr']*100):.1f}%" if benchmark_stats else None
        cpa_delta = f"{((curr_cpa - benchmark_stats['avg_cpa'])/benchmark_stats['avg_cpa']*100):.1f}%" if benchmark_stats else None

        m1.metric("총 소진액", f"{df['소진액'].sum():,.0f}원")
        m2.metric("평균 CTR", f"{curr_ctr:.2f}%", delta=ctr_delta)
        m3.metric("평균 CPA", f"{curr_cpa:,.0f}원", delta=cpa_delta, delta_color="inverse")
        m4.metric("총 전환수", f"{df['전환수'].sum():,.0f}건")

        if '매체' in df.columns:
            st.plotly_chart(px.bar(df, x='매체', y='소진액', color='CPA', color_continuous_scale="Oranges"), width='stretch')

    with t3:
        if st.button("AI 전략 리포트 생성"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"데이터 기반 분석해줘: {df.head(10).to_string()}")
            st.markdown(res.text)

else:
    # 벤치마크 상태 표시 (디버깅용)
    if not benchmark_stats:
        st.warning(f"⚠️ 벤치마크 파일을 찾을 수 없거나 형식이 잘못되었습니다. (찾은 경로: {benchmark_path})")
    st.info("파일을 업로드하면 브레인큐브 26년 평균 데이터와 비교 분석을 시작합니다.")
