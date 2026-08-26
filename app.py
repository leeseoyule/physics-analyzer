import streamlit as st
from PIL import Image
import google.generativeai as genai

st.set_page_config(
    page_title="세상의 모든 물체: AI 비전 물리 분석기",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 세상의 모든 물체: AI 물리 분석기")
st.write("내가 보고 있는 이 물체에는 지금 어떤 힘이 작용하고 있을까.. 궁금하지 않으셨나요? 사진을 업로드 하시면 **Gemini AI**가 사진 속 물체를 분석하고, 눈에 보이지 않는 힘과 물리 법칙을 계산해 드립니다!")

# 💡 Streamlit Secrets에서 API 키를 자동으로 안전하게 가져옴
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    api_key = None

# 사진 업로드 기능
uploaded_file = st.file_uploader("분석할 물체 사진을 올려주세요!", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 물체", use_container_width=True)
    
    st.markdown("---")
    
    if st.button("🚀 AI 비전 힘 분석 및 시뮬레이션 실행"):
        if not api_key:
            st.warning("⚠️ Streamlit Secrets에 API 키가 설정되어 있지 않습니다!")
        else:
            with st.spinner("🤖 AI가 사진을 정밀 분석하고 물리 법칙을 계산 중입니다..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    
                    prompt = """
                    당신은 물리학자이자 AI 비전 분석가입니다. 업로드된 사진 속 물체를 보고 다음 항목들을 분석해주세요:
                    1. 사진 속 물체가 무엇인지 정확히 식별하고 설명해주세요.
                    2. 이 물체의 예상 재질(예: 화강암, 콘크리트, 목재, 금속 등)과 대략적인 크기(높이 미터 단위)를 추정해주세요.
                    3. 이 물체의 추정 질량(kg)을 대략적으로 계산해주세요.
                    4. 무게중심과 힘의 평형, 조화 진동(Harmonic Oscillation) 관점에서 이 물체가 안정적인지 분석해주세요.
                    
                    답변은 친절하고 전문적인 톤으로 작성해주되, Markdown 형식을 사용하여 깔끔하게 정리해주세요.
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    st.success("✨ AI 비전 분석이 완료되었습니다!")
                    st.markdown("### 📊 AI 물리 리포트")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {e}")
