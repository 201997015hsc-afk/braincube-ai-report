import streamlit as st
import os
import pandas as pd

st.title("🔍 브레인큐브 서버 파일 진단 모드")

# 1. 서버에 있는 모든 파일을 샅샅이 뒤져서 리스트로 만듭니다.
file_tree = []
for root, dirs, files in os.walk("."):
    for file in files:
        # 파일의 전체 경로를 기록합니다.
        file_tree.append(os.path.join(root, file))

st.write("### 📍 현재 서버가 읽을 수 있는 모든 파일 목록")
if file_tree:
    # 찾은 파일들을 보기 좋게 표로 보여줍니다.
    st.table(pd.DataFrame(file_tree, columns=["파일 경로"]))
else:
    st.error("서버에 아무 파일도 보이지 않습니다. (연결 오류 가능성)")

st.write("---")
st.info("위 목록에서 'benchmark.csv'와 'braincube_logo.png'가 포함된 **정확한 경로**를 복사해서 알려주세요!")
