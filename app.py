import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import json
import math

# 페이지 설정
st.set_page_config(page_title="범용 스마트 벡터 물리 시뮬레이터", page_icon="🪨", layout="wide")

st.title("🌍 범용 스마트 벡터 물리 & 힘 시뮬레이터")
st.write("어떤 물체 사진이든 업로드하고, 무게 입력 방식을 선택한 뒤 **외력의 크기와 각도**에 따른 물리 분해 및 시뮬레이션을 실행해보세요!")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ Streamlit Secrets에 `GEMINI_API_KEY`가 설정되어 있지 않습니다.")
    st.stop()

# 1. 사진 업로드
uploaded_file = st.file_uploader("분석할 물체 사진을 올려주세요 (예: 흔들바위, 피규어, 의자 등)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.markdown("---")
    st.subheader("⚙️ 1단계: 물체 및 무게 설정 방식 선택")
    
    # [요청하신 부분] 사진 입력 칸 바로 밑에 무게 입력 방식 선택 칸 배치
    weight_mode = st.radio(
        "물체의 이름과 무게를 어떻게 설정하시겠습니까?", 
        ["직접 입력할래요", "잘 모르겠어요 (AI에게 물체 인식 및 무게 추정 맡기기)"],
        horizontal=True
    )
    
    object_name = "물체"
    actual_mass = 100.0
    
    # 세션 상태 관리 (사진이 바뀌거나 모드 변경 시 초기화)
    if "last_file" not in st.session_state or st.session_state["last_file"] != uploaded_file.name:
        st.session_state["last_file"] = uploaded_file.name
        st.session_state["ai_analyzed"] = False

    if weight_mode == "직접 입력할래요":
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            object_name = st.text_input("물체의 이름", value="흔들바위")
        with col_m2:
            actual_mass = st.number_input("물체의 질량 (kg)", min_value=0.01, max_value=1000000.0, value=5000.0, step=10.0)
    else:
        st.info("💡 'AI에게 추정 맡기기'를 선택하셨습니다. 아래 분석 버튼을 누르면 AI가 사진을 판독합니다.")
        
        if not st.session_state.get("ai_analyzed", False):
            if st.button("🤖 AI로 물체 인식 및 무게 자동 추정 실행"):
                with st.spinner("AI가 사진 속 물체를 분석하고 이름과 질량을 추정하는 중..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = """
                        이 사진 속의 주요 물체를 분석해줘. 다음 정보를 반드시 JSON 형식으로만 답해줘. 다른 말은 쓰지 마.
                        1. "name": 물체의 이름 (예: 흔들바위, 피규어, 자동차, 의자 등)
                        2. "mass": 이 물체의 실제 대략적인 질량 (kg 단위 숫자만, 예: 작은 소품이면 0.5, 거대한 바위나 건물류면 5000 등)
                        형식 예시: {"name": "흔들바위", "mass": 5000}
                        """
                        res = model.generate_content([prompt, image])
                        clean_text = res.text.replace("```json", "").replace("
