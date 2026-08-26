%%writefile app.py
import streamlit as st
from PIL import Image, ImageDraw
import google.generativeai as genai
import json

# 앱 타이틀 및 소개
st.title("🪨 세상의 모든 물체: 물리 & 힘 분석기 (AI 스마트 버전)")
st.write("사진을 올리고 무게를 직접 입력하거나, 모를 경우 **AI 멀티모달 분석**에 맡겨보세요!")

# 사이드바 또는 상단에 API 키 입력 설정 (Gemini 연동용)
with st.sidebar:
    st.subheader("🔑 AI 설정")
    api_key = st.text_input("Google Gemini API 키 입력", type="password")
    st.caption("AI 자동 추정 기능을 쓰려면 Google AI Studio에서 발급받은 API 키를 입력하세요.")

# 사진 업로드 기능
uploaded_file = st.file_uploader("분석할 물체 사진을 올려주세요! (예: 흔들바위, 치이카와 인형 등)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.markdown("---")
    st.subheader("⚙️ 물리 변수 설정")
    
    # 무게를 아는지 모르는지 선택하는 옵션
    weight_mode = st.radio(
        "물체의 무게를 알고 계시나요?", 
        ["직접 입력할래요", "잘 모르겠어요 (AI가 사진을 보고 추정)"]
    )
    
    object_name = "분석된 물체"
    actual_mass = 1.0 # 기본값
    
    if weight_mode == "직접 입력할래요":
        object_name = st.text_input("물체의 이름", value="내 물건")
        actual_mass = st.number_input("물체의 실제 질량 (kg)", min_value=0.01, max_value=10000.0, value=1.0, step=0.5)
    else:
        st.info("💡 '모름'을 선택하셨습니다. 분석 버튼을 누르면 AI가 사진 속 물체를 판독해 자동으로 무게를 추정합니다!")
        object_name = st.text_input("물체의 대략적인 이름 (선택사항)", value="사진 속 물체")

    # 물리 분석 버튼
    if st.button("🚀 힘 분석 및 벡터 시각화 실행"):
        
        # '모름'을 선택했고 AI를 써야 하는 경우
        if weight_mode == "잘 모르겠어요 (AI가 사진을 보고 추정)":
            if not api_key:
                st.error("⚠️ AI 자동 추정을 사용하려면 좌측 사이드바에 Gemini API 키를 입력해주세요!")
                st.stop()
            
            with st.spinner("🤖 Gemini AI가 사진을 분석하여 물체와 질량을 추정하는 중..."):
                try:
                    genai.configure(api_key=api_key)
                    # 최신 멀티모달 모델 설정
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """
                    이 사진 속 물체를 분석해줘. 다음 두 가지 정보를 반드시 JSON 형식으로만 답해줘. 다른 말은 쓰지 마.
                    1. "name": 물체의 정확한 이름 (예: 치이카와 인형, 화강암 바위 등)
                    2. "mass": 이 물체의 실제 대략적인 질량(kg 단위 숫자만, 예: 0.3, 50, 1500 등)
                    형식 예시: {"name": "치이카와 인형", "mass": 0.2}
                    """
                    response = model.generate_content([prompt, image])
                    
                    # 텍스트 결과에서 JSON 파싱 시도
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    ai_data = json.loads(clean_text)
                    
                    object_name = ai_data.get("name", "알 수 없는 물체")
                    actual_mass = float(ai_data.get("mass", 1.0))
                    
                    st.success(f"✨ AI 분석 성공! 인식된 물체: **{object_name}** / 추정 질량: **{actual_mass} kg**")
                except Exception as e:
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")
                    st.stop()
        
        # 공통 물리 계산 및 벡터 시각화 로직
        with st.spinner("물리 법칙 적용 및 벡터 시뮬레이션 중..."):
            g = 9.8  # 중력가속도
            gravity_force = actual_mass * g
            
            # 이미지 위에 벡터(화살표) 그리기
            img_draw = image.copy()
            draw = ImageDraw.Draw(img_draw)
            width, height = img_draw.size
            cx, cy = width // 2, height // 2
            
            arrow_length = min(width, height) // 4
            
            # 중력 벡터 (빨간색 - 아래)
            draw.line([(cx, cy), (cx, cy + arrow_length)], fill="red", width=max(4, width // 100))
            draw.polygon([(cx, cy + arrow_length), (cx - 10, cy + arrow_length - 20), (cx + 10, cy + arrow_length - 20)], fill="red")
            
            # 수직항력 벡터 (파란색 - 위)
            draw.line([(cx, cy), (cx, cy - arrow_length)], fill="blue", width=max(4, width // 100))
            draw.polygon([(cx, cy - arrow_length), (cx - 10, cy - arrow_length + 20), (cx + 10, cy - arrow_length + 20)], fill="blue")
            
            # 결과 출력
            st.image(img_draw, caption=f"'{object_name}' 힘 벡터 분석 (빨강: 중력 {gravity_force:.1f}N / 파랑: 수직항력)", use_column_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="최종 적용 질량", value=f"{actual_mass} kg")
            with col2:
                st.metric(label="작용 중력 ($F=mg$)", value=f"{gravity_force:,.1f} N")
                
            st.markdown("### 📊 물리 리포트 요약")
            st.write(f"- **대상 물체:** {object_name}")
            st.write(f"- **힘의 평형:** 중력({gravity_force:.1f}N)과 바닥이 밀어내는 수직항력이 평형을 이루고 있습니다.")
            st.info("💡 **결론:** 사용자가 무게를 몰라 '모름'을 선택하더라도, 멀티모달 AI가 캐릭터나 돌덩이의 정체를 파악해 알맞은 무게와 물리 벡터를 시각화해 줍니다!")
