import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import json
import math

# 페이지 설정
st.set_page_config(page_title="물리 시뮬레이터", page_icon="🪨", layout="wide")

# ==========================================
# 🎨 UI/UX: PC는 이미지 커서, 모바일은 터치 고양이 이모지 적용
# ==========================================
st.markdown("""
<style>
.stApp {
    background-color: #FFFDF0;
    color: #2C2C2C;
    /* PC 브라우저용 고양이 이미지 커서 */
    cursor: url('https://raw.githubusercontent.com/leeseoyule/physics-analyzer/main/cat.png') 16 16, auto;
}

div.stButton > button {
    background: linear-gradient(135deg, #FFD166 0%, #FFB703 100%);
    color: #2C2C2C;
    font-weight: bold;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    cursor: url('https://raw.githubusercontent.com/leeseoyule/physics-analyzer/main/cat.png') 16 16, pointer;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #FFB703 100%, #FB8500 100%);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0,0,0,0.1);
}

div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    border: 1px solid #FDF0D5;
}

h1, h2, h3 {
    color: #333333;
}

/* 모바일 전용 손가락 따라다니는 고양이 이모지 스타일 */
#mobile-cat {
    position: fixed;
    pointer-events: none;
    font-size: 32px;
    z-index: 99999;
    transform: translate(-50%, -50%);
    display: none;
}
</style>

<!-- 모바일 터치 추적용 고양이 이모지 -->
<div id="mobile-cat">🐱</div>

<script>
// 모바일 기기인지 간단히 확인
const isMobile = /Mobi|Android|iPhone/i.test(navigator.userAgent);

if (isMobile) {
    const mCat = document.getElementById('mobile-cat');

    // 손가락으로 화면을 터치하고 움직일 때
    window.addEventListener('touchmove', (e) => {
        if (e.touches.length > 0) {
            mCat.style.display = 'block';
            mCat.style.left = e.touches[0].clientX + 'px';
            mCat.style.top = e.touches[0].clientY + 'px';
        }
    }, { passive: true });

    // 화면을 터치하는 순간
    window.addEventListener('touchstart', (e) => {
        if (e.touches.length > 0) {
            mCat.style.display = 'block';
            mCat.style.left = e.touches[0].clientX + 'px';
            mCat.style.top = e.touches[0].clientY + 'px';
        }
    }, { passive: true });

    // 터치를 뗄 때 고양이 숨기기
    window.addEventListener('touchend', () => {
        mCat.style.display = 'none';
    });
}
</script>
""", unsafe_allow_html=True)

# 상단 안내 문구
st.title("벡터 물리 & 힘 시뮬레이터 🐱")
st.write("어떤 물체 사진이든 업로드하고, 무게를 설정한 뒤 **외력의 크기(최대 2000N)**와 각도에 따른 종합적인 힘의 상쇄 및 벡터 분해 시뮬레이션을 확인해보세요!")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ Streamlit Secrets에 `GEMINI_API_KEY`가 설정되어 있지 않습니다.")
    st.stop()

# 1. 사진 업로드
uploaded_file = st.file_uploader("분석할 물체 사진을 올려주세요 (예: 흔들바위, 피규어, 의자 등)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)

    # 사진 크기 최적화
    max_size = 800
    image.thumbnail((max_size, max_size))

    st.markdown("---")
    st.subheader("물체 및 무게 설정 방식 선택")

    weight_mode = st.radio(
        "물체의 이름과 무게를 어떻게 설정하시겠습니까?", 
        ["직접 입력할래요", "잘 모르겠어요 (AI에게 물체 인식 및 무게 추정 맡기기)"],
        horizontal=True
    )

    object_name = "물체"
    actual_mass = 100.0

    # 세션 상태 관리
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
        st.info("'AI에게 추정 맡기기'를 선택하셨습니다. 아래 분석 버튼을 누르면 AI가 사진을 판독합니다.")

        if not st.session_state.get("ai_analyzed", False):
            if st.button("AI로 물체 인식 및 무게 자동 추정 실행"):
                with st.spinner("AI가 사진 속 물체를 분석하고 이름과 질량을 추정하는 중..."):
                    try:
                        genai.configure(api_key=API_KEY)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = '이 사진 속의 주요 물체를 분석해줘. 다음 정보를 반드시 JSON 형식으로만 답해줘. 다른 말은 쓰지 마. 1. "name": 물체의 이름 2. "mass": 이 물체의 실제 대략적인 질량 (kg 단위 숫자만). 형식 예시: {"name": "흔들바위", "mass": 5000}'

                        res = model.generate_content([prompt, image])
                        clean_text = res.text.replace("```json", "").replace("
