import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from docx import Document
import io
import datetime

# 1. 보안 및 페이지 설정
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
st.set_page_config(page_title="브레인큐브 AI 리포트", layout="wide")

# 2. 로고 및 타이틀 (중앙 배치 스타일)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        # 파일명이 braincube_logo.png 인지 꼭 확인해주세요!
        st.image("braincube_logo.png", width=300) 
    except:
        st.title("🍊 BRAINCUBE") # 로고 없을 때 대안 문구
    st.markdown("<h1 style='text-align: center;'>AI 캠페인 분석 솔루션</h1>", unsafe_allow_html=True)
    st.write("---")

# 3. 데이터 로드 (벤치마크)
@st.cache_data
def load_benchmark():
    try:
        # 깃허브에 대문자로 시작하는 Benchmark.csv 라면 이름을 맞춰주세요!
        return pd.read_csv("benchmark.csv") 
    except:
        return None

benchmark_df = load_benchmark()

# 4. 메인 화면에 파일 업로드 배치 (사이드바 아님!)
st.subheader("📂 데이터 분석 시작")
uploaded_file = st.file_uploader("캠페인 로우데이터(CSV/XLSX)를 드래그하거나 클릭하여 업로드하세요", type=["csv", "xlsx"])

if uploaded_file:
    # 데이터 읽기
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success(f"✅ '{uploaded_file.name}' 분석 준비 완료!")

    # --- 대시보드 탭 구성 ---
    tab1, tab2, tab3 = st.tabs(["📊 성과 요약", "🎨 소재 분석", "🤖 AI 리포트"])

    with tab1:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 소진액", f"{df['소진액'].sum():,}원")
        m2.metric("평균 CTR", f"{df['CTR'].mean():.2f}%")
        m3.metric("평균 CPA", f"{df['CPA'].mean():,.0f}원")
        m4.metric("총 전환수", f"{df['전환수'].sum():,}건")

        fig_media = px.bar(df, x='매체', y='소진액', color='CPA', title="매체별 예산 대비 효율", color_continuous_scale="Oranges")
        st.plotly_chart(fig_media, width='stretch')

    with tab2:
        top_creatives = df.sort_values(by='CPA', ascending=True).head(5)
        fig_creative = px.bar(top_creatives, x='소재명', y='CTR', color='CPA', title="Top 5 위닝 크리에이티브")
        st.plotly_chart(fig_creative, width='stretch')
        st.table(top_creatives[['소재명', 'CTR', 'CPA', '전환수']])

    with tab3:
        if st.button("AI 전략 분석 시작"):
            with st.spinner("브레인큐브 AI가 데이터를 분석 중입니다..."):
                raw_summary = df.groupby('매체').agg({'소진액':'sum', 'CPA':'mean', '전환수':'sum'}).to_string()
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"마케팅 전문가로서 분석해줘: {raw_summary}")
                st.markdown(response.text)
                
                # 워드 다운로드
                doc = Document()
                doc.add_heading('브레인큐브 AI 분석 리포트', 0)
                doc.add_paragraph(response.text)
                bio = io.BytesIO()
                doc.save(bio)
                st.download_button("📄 리포트 다운로드(.docx)", bio.getvalue(), f"Report_{datetime.date.today()}.docx")

else:
    # 파일 업로드 전 가이드 문구
    st.info("광고주 캠페인 리포트를 업로드하시면 AI가 즉시 분석을 시작합니다.")

st.markdown("---")
st.caption("© 2026 Braincube AI Marketing Solutions.")
