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

# 🔥 [핵심] 파일 추적 엔진: 어떤 경로에 있든 파일을 찾아냅니다.
def get_absolute_path(filename):
    # 1. 현재 실행중인 app.py 주변을 먼저 찾습니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path1 = os.path.join(current_dir, filename)
    if os.path.exists(path1): return path1
    
    # 2. 알려주신 특정 경로를 직접 확인합니다.
    path2 = f"./AI_Report/{filename}"
    if os.path.exists(path2): return path2
    
    # 3. 전체 프로젝트를 다 뒤져서 대소문자 무시하고 찾습니다.
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.lower() == filename.lower():
                return os.path.join(root, f)
    return None

# 파일 경로 확정
final_logo_path = get_absolute_path("braincube_logo.png")
final_benchmark_path = get_absolute_path("benchmark.csv")

# 벤치마크 데이터 로드 (한글 깨짐 완벽 방어)
@st.cache_data
def load_benchmark_safe(path):
    if not path: return None
    # 한글 인코딩 후보들 (엑셀 저장 방식에 따라 다름)
    encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
    for enc in encodings:
        try:
            b_df = pd.read_csv(path, encoding=enc)
            b_df.columns = [c.strip() for c in b_df.columns]
            
            # 컬럼 매칭 (대소문자/한글 모두 대응)
            c_map = {'CPA': ['평균 CPA', 'CPA', '전환단가', 'avg_cpa'], 
                     'CTR': ['평균 CTR', 'CTR', '클릭률', 'avg_ctr']}
            for target, cands in c_map.items():
                for c in cands:
                    if c in b_df.columns:
                        b_df.rename(columns={c: target}, inplace=True)
                        break
            
            # 수치 데이터로 변환
            avg_cpa = pd.to_numeric(b_df['CPA'], errors='coerce').mean()
            avg_ctr = pd.to_numeric(b_df['CTR'], errors='coerce').mean()
            return {'avg_cpa': avg_cpa, 'avg_ctr': avg_ctr}
        except:
            continue
    return None

benchmark_stats = load_benchmark_safe(final_benchmark_path)

# --- 상단 레이아웃 ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if final_logo_path:
        st.image(final_logo_path, width=300) 
    else:
        st.markdown("<h1 style='text-align: center; color: orange;'>BRAINCUBE</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>AI 캠페인 분석 솔루션</h2>", unsafe_allow_html=True)
    st.write("---")

# --- 메인 분석 로직 ---
uploaded_file = st.file_uploader("📊 광고주 캠페인 리포트를 업로드하세요", type=["csv", "xlsx"])

if uploaded_file:
    # 사용자 파일 로드
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    
    # 사용자 파일 컬럼 매칭
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
    t1, t2, t3 = st.tabs(["📈 핵심 성과", "🎨 소재 효율", "🤖 AI 리포트"])
    
    with t1:
        st.subheader("종합 퍼포먼스 (vs 26년 평균)")
        m1, m2, m3, m4 = st.columns(4)
        curr_ctr, curr_cpa = df['CTR'].mean(), df['CPA'].mean()
        
        # 벤치마크 Delta 계산 (CPA는 낮을수록 좋음)
        ctr_delta = f"{((curr_ctr - benchmark_stats['avg_ctr'])/benchmark_stats['avg_ctr']*100):.1f}%" if benchmark_stats else None
        cpa_delta = f"{((curr_cpa - benchmark_stats['avg_cpa'])/benchmark_stats['avg_cpa']*100):.1f}%" if benchmark_stats else None

        m1.metric("총 소진액", f"{df['소진액'].sum():,.0f}원")
        m2.metric("평균 CTR", f"{curr_ctr:.2f}%", delta=ctr_delta)
        m3.metric("평균 CPA", f"{curr_cpa:,.0f}원", delta=cpa_delta, delta_color="inverse")
        m4.metric("총 전환수", f"{df['전환수'].sum():,.0f}건")

        if '매체' in df.columns:
            st.plotly_chart(px.bar(df, x='매체', y='소진액', color='CPA', title="매체별 현황", color_continuous_scale="Oranges"), width='stretch')

    with t3:
        if st.button("AI 전략 리포트 생성"):
            with st.spinner("분석 중..."):
                summary = df.groupby('매체').agg({'소진액':'sum', 'CPA':'mean', '전환수':'sum'}).to_string()
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"광고 대행사 마케터로서 분석해줘: {summary}")
                st.markdown(res.text)

else:
    # 📌 하단 상태창 (관리자용 확인 메시지)
    st.write("---")
    if benchmark_stats:
        st.success(f"🔗 26년 평균 데이터 연결 성공! (위치: {final_benchmark_path})")
    else:
        st.warning(f"⚠️ 벤치마크 데이터를 찾는 중입니다. (현재 확인된 경로: {final_benchmark_path})")
    st.info("광고주 리포트를 업로드하면 즉시 분석이 시작됩니다.")

st.markdown("---")
st.caption("© 2026 Braincube AI Marketing Solutions.")
