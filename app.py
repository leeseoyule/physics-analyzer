import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import json
import math
import random

# 페이지 설정
st.set_page_config(page_title="스마트 벡터 물리 시뮬레이터", page_icon="🪨", layout="wide")

# ==========================================
# 🎨 UI/UX 커스텀 스타일 (연한 노란색 테마)
# ==========================================
st.markdown("""
    <style>
    /* 전체 배경을 따뜻한 연한 노란색으로 설정 */
    .stApp {
        background-color: #FFFDF0;
        color: #2C2C2C;
    }
    
    /* 버튼 스타일링 */
    div.stButton > button {
        background: linear-gradient(135deg, #FFD166 0%, #FFB703 100%);
        color: #2C2C2C;
        font-weight: bold;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #FFB703 100%, #FB8500 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.1);
    }

    /* 메트릭 박스 스타일 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        border: 1px solid #FDF0D5;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🐱 양자역학 고양이 상호작용 세션
# ==========================================
if "cat_clicks" not in st.session_state:
    st.session_state["cat_clicks"] = 0

cat_quotes = [
    "📦 \"슈뢰딩거의 고양이가 상자 속에서 힘의 평형을 고민 중입니다!\"",
    "✨ \"관측하기 전까지 이 물체는 움직이고 있으면서도 멈춰 있습니다.\"",
    "🐾 \"집사야, 외력을 줄 때 조심해줘!\"",
    "🌀 \"파동함수가 붕괴되었습니다! 벡터 분해를 시작하죠.\""
]

# 상단 레이아웃 (제목 + 고양이 상호작용 버튼)
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("스마트 벡터 물리 & 힘 시뮬레이터")
    st.write("어떤 물체 사진이든 업로드하고, 무게를 설정한 뒤 **외력의 크기(최대 2000N)**와 각도에 따른 종합적인 힘의 상쇄 및 벡터 분해 시뮬레이션을 확인해보세요!")
with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🐱 양자 고양이 쓰다듬기"):
        st.session_state["cat_clicks"] += 1

if st.session_state["cat_clicks"] > 0:
    current_quote = random.choice(cat_quotes)
    st.info(f"양자 고양이 상태 (상호작용 횟수: {st.session_state['cat_clicks']}회): {current_quote}")

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
                        clean_text = res.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)

                        st.session_state["ai_name"] = data.get("name", "인식된 물체")
                        st.session_state["ai_mass"] = float(data.get("mass", 100.0))
                        st.session_state["ai_analyzed"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI 분석 중 오류가 발생했습니다: {e}")

        if st.session_state.get("ai_analyzed", False):
            object_name = st.session_state.get("ai_name", "물체")
            actual_mass = st.session_state.get("ai_mass", 100.0)
            st.success(f"AI 분석 완료! 인식된 물체: **{object_name}** / 추정 질량: **{actual_mass:,.1f} kg**")
        else:
            object_name = "AI 분석 대기 중인 물체"
            actual_mass = 1000.0

    st.markdown("---")
    st.subheader("외부 힘(Vector Force) 사용자 정의 설정")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        # 외력 최대 크기를 2000N으로 제한
        force_magnitude = st.slider(
            "가하고 싶은 외력의 크기 (N)", 
            min_value=0.0, max_value=2000.0, value=200.0, step=10.0,
            help="최대 2000N까지 설정 가능합니다. (100N = 약 10kg을 미는 힘)"
        )
    with col_f2:
        force_angle = st.slider(
            "미는 방향 각도 (수평 기준, °)", 
            min_value=-90.0, max_value=90.0, value=0.0, step=5.0,
            help="0°: 수평 밀기 / 양수(+): 위에서 아래로 내리누름 / 음수(-): 아래에서 위로 치켜올림"
        )

    # 물리 시뮬레이션 실행 버튼
    if st.button("벡터 분해 및 물리 시뮬레이션 실행"):
        with st.spinner("삼각함수 벡터 분해 및 상쇄 시뮬레이션 생성 중..."):
            g = 9.8
            gravity_force = actual_mass * g # 중력 (N)

            # 삼각함수를 통한 수평힘 / 수직힘 벡터 분해
            angle_rad = math.radians(force_angle)
            horizontal_force = force_magnitude * math.cos(angle_rad) # 수평 성분 (Fx)
            vertical_force = force_magnitude * math.sin(angle_rad)    # 수직 성분 (Fy)

            # 상쇄되는 힘 및 반작용 계산
            effective_normal_force = gravity_force + vertical_force
            counter_horizontal_force = -horizontal_force 

            stability_ratio = (force_magnitude / max(1.0, gravity_force * 0.5)) * 100

            # 이미지 드로잉 준비 (화살표를 물체 크기만큼 대폭 키움)
            img_eq = image.copy()
            draw_eq = ImageDraw.Draw(img_eq)
            w, h = image.size
            cx, cy = w // 2, h // 2

            # 화살표 길이를 물체 크기 수준(이미지 치수의 60%)으로 설정
            arrow_len = int(min(w, h) * 0.6)

            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48) # 폰트 크기 확대
            except:
                font = ImageFont.load_default()

            # 1. 평형 상태 이미지 (중력 & 수직항력)
            draw_eq.line([(cx, cy), (cx, cy + arrow_len)], fill="red", width=15)
            draw_eq.text((cx + 20, cy + arrow_len // 2), f"중력\n({gravity_force:,.0f}N)", fill="red", font=font)

            draw_eq.line([(cx, cy), (cx, cy - arrow_len)], fill="blue", width=20)
            draw_eq.text((cx + 20, cy - arrow_len // 2 - 30), f"수직항력\n({gravity_force:,.0f}N)", fill="blue", font=font)

            # 2. 시뮬레이션 이미지 (기존 힘 + 외력 + 상쇄되는 힘 동시 표시)
            img_sim = image.copy()
            draw_sim = ImageDraw.Draw(img_sim)

            if force_magnitude > 0:
                # A. 외력 벡터 (초록색)
                dx = int(arrow_len * math.cos(angle_rad))
                dy = int(arrow_len * math.sin(angle_rad))
                start_x, start_y = cx - dx, cy + dy

                draw_sim.line([(start_x, start_y), (cx, cy)], fill="green", width=10)
                draw_sim.text((start_x - 10, start_y - 45), f"외력 F: {force_magnitude:,.0f}N ({force_angle}°)", fill="green", font=font)

                # B. 수평 방향 상쇄력 / 마찰력 (보라색)
                counter_x = cx + int(arrow_len * 0.8 * (-1 if horizontal_force >= 0 else 1))
                draw_sim.line([(cx, cy + 20), (counter_x, cy + 20)], fill="purple", width=20)
                draw_sim.text((counter_x if counter_x < cx else cx, cy + 30), f"상쇄/마찰력\n({counter_horizontal_force:+,.0f}N)", fill="purple", font=font)

                # C. 수직 분해 및 변동된 수직항력 (주황색)
                v_end_y = cy - int(arrow_len * 0.8 * (effective_normal_force / max(1.0, gravity_force)))
                draw_sim.line([(cx + 40, cy), (cx + 40, v_end_y)], fill="orange", width=8)
                draw_sim.text((cx + 60, (cy + v_end_y)//2), f"변동 수직항력\n({effective_normal_force:,.0f}N)", fill="orange", font=font)

            # 레이아웃 출력
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("기본 힘의 평형 상태")
                st.image(img_eq, caption=f"'{object_name}' 정적 평형", use_container_width=True)

            with col2:
                st.subheader("힘의 상쇄 및 벡터 분해 시뮬레이션")
                st.image(img_sim, caption=f"외력 크기: {force_magnitude}N / 각도: {force_angle}°", use_container_width=True)

            # 상세 분석 리포트
            st.markdown("### 정밀 힘의 상쇄 및 벡터 분해 리포트")
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                st.metric(label="설정된 외력 (Force)", value=f"{force_magnitude:,.1f} N ({force_angle}°)")
            with c_m2:
                st.metric(label="수평힘 및 상쇄력 (Fx)", value=f"{horizontal_force:,.1f} N", delta=f"상쇄: {counter_horizontal_force:+,.1f}N")
            with c_m3:
                st.metric(label="최종 수직항력 (Fy 반영)", value=f"{effective_normal_force:,.1f} N", delta=f"변동: {vertical_force:+,.1f}N")

            # 안정성 평가 바
            st.progress(min(max(stability_ratio, 0), 100) / 100.0, text=f"물체 질량 대비 외력 부하율: {stability_ratio:.1f}%")

            if stability_ratio > 50:
                st.error("🚨 **결과 예측:** 가해진 힘이 물체의 무게 대비 상대적으로 커서 상쇄 한계를 넘어서고 밀려나거나 쓰러질 위험이 높습니다!")
            else:
                st.success("✨ **결과 예측:** 마찰력 및 지지력의 상쇄 범위 내에 있어 물체가 안전하게 버티거나 평형을 유지합니다.")
