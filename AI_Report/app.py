import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from docx import Document
from docx.shared import Inches
import io
import datetime

# 1. 보안 설정: Streamlit Secrets에서 API 키를 안전하게 가져옵니다.
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 2. 페이지 설정 (브레인큐브 스타일)
st.set_page_config(page_title="브레인큐브 AI 리포트 고도화", layout="wide")

# 로고 및 타이틀
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("braincube_logo.png", width=150)
    except:
        st.write("[로고 이미지]")
with col2:
    st.title("🚀 브레인큐브 AI 캠페인 분석 솔루션")
    st.caption("Data-Driven Insights for Your Next Campaign")

# 3. 데이터 로드 및 벤치마크 (로컬 파일 연결)
@st.cache_data
def load_benchmark():
    try:
        return pd.read_csv("benchmark.csv")
    except:
        return None

benchmark_df = load_benchmark()

# 4. 사이드바 - 파일 업로드
st.sidebar.header("📊 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("캠페인 로우데이터(CSV/XLSX)를 올려주세요", type=["csv", "xlsx"])

if uploaded_file:
    # 데이터 읽기
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 기본 전처리 (예시 컬럼명 기준)
    st.success(f"'{uploaded_file.name}' 로드 완료!")

    # --- 메인 대시보드 시작 ---
    tab1, tab2, tab3 = st.tabs(["📈 성과 요약", "🎨 소재 분석", "🤖 AI 인사이트"])

    with tab1:
        st.subheader("캠페인 퍼포먼스 요약")
        # 메트릭 표시 (예시 데이터 기반)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 소진액", f"{df['소진액'].sum():,}원")
        m2.metric("평균 CTR", f"{df['CTR'].mean():.2f}%")
        m3.metric("평균 CPA", f"{df['CPA'].mean():,}")
        m4.metric("총 전환수", f"{df['전환수'].sum():,}")

        # 매체별 효율 차트 (기존 use_container_width -> width='stretch' 변경)
        fig_media = px.bar(df, x='매체', y='소진액', color='CPA', title="매체별 예산 대비 효율")
        st.plotly_chart(fig_media, width='stretch')

    with tab2:
        st.subheader("핵심 소재(Creative) 랭킹")
        # 소재별 랭킹 대시보드 시각화
        top_creatives = df.sort_values(by='CPA', ascending=True).head(5)
        fig_creative = px.bar(top_creatives, x='소재명', y='CTR', color='CPA', 
                             title="Top 5 위닝 크리에이티브 (CPA 낮은 순)")
        st.plotly_chart(fig_creative, width='stretch')
        
        st.table(top_creatives[['소재명', 'CTR', 'CPA', '전환수']])

    with tab3:
        st.subheader("AI 전략 리포트 생성")
        if st.button("AI 분석 리포트 추출하기"):
            with st.spinner("AI가 데이터를 분석하여 전략을 수립 중입니다..."):
                # AI 분석 프롬프트 구성
                raw_data_summary = df.groupby('매체').agg({'소진액':'sum', 'CPA':'mean', '전환수':'sum'}).to_string()
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"""
                광고 대행사 브레인큐브의 시니어 마케터로서 아래 데이터를 분석해줘.
                데이터: {raw_data_summary}
                
                보고서 형식:
                1. 전월 성과 총평
                2. 고효율 매체 및 소재 발굴 결과
                3. 차월 예산 재배분 전략 (Next Step)
                """)
                
                st.markdown(response.text)
                
                # 워드 다운로드 기능
                doc = Document()
                doc.add_heading('브레인큐브 AI 캠페인 분석 리포트', 0)
                doc.add_paragraph(response.text)
                
                bio = io.BytesIO()
                doc.save(bio)
                st.download_button(
                    label="📄 워드 리포트 다운로드",
                    data=bio.getvalue(),
                    file_name=f"Braincube_AI_Report_{datetime.date.today()}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

else:
    st.info("왼쪽 사이드바에서 데이터를 업로드하면 분석이 시작됩니다.")
    # 샘플 이미지나 안내 문구
    st.image("https://via.placeholder.com/800x400.png?text=Waiting+for+Data+Upload", width='stretch')

# 하단 푸터
st.markdown("---")
st.caption("© 2026 Braincube AI Marketing Solutions. All rights reserved.")
