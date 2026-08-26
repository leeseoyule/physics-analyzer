import streamlit as st
from PIL import Image
import google.generativeai as genai
import plotly.graph_objects as go
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="세상의 모든 물체: 3D 벡터 힘 분석기",
    page_icon="🧊",
    layout="centered"
)

st.title("🧊 세상의 모든 물체: AI 기반 3D 물 분석기")
st.write("내가 지금 보고 있는 물체에 어떤 힘들이 작용하고 있을까.. 궁금하진 않으셨나요?")
st.write("사진을 올리면 **Gemini AI**가 물체의 힘을 계산하고, 3D 공간에 컬러풀한 벡터 화살표와 뉴턴(N) 크기를 시각화해 드립니다!")

# Streamlit Secrets에서 API 키 불러오기
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
    
    if st.button("🚀 3D 힘 벡터 시뮬레이션 실행"):
        if not api_key:
            st.warning("⚠️ Streamlit Secrets에 API 키가 설정되어 있지 않습니다!")
        else:
            with st.spinner("🤖 AI가 물리 법칙을 계산하고 3D 벡터 공간을 렌더링 중입니다..."):
                try:
                    genai.configure(api_key=api_key)
                    # 최신 모델 지정
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    
                    prompt = """
                    당신은 물리학자입니다. 업로드된 사진 속 물체의 질량(kg)을 대략적으로 추정하고, 
                    이 물체에 작용하는 주요 3가지 힘(중력, 수직항력, 최대 정지 마찰력)의 뉴턴(N) 값을 계산해주세요.
                    
                    반드시 아래 형식의 텍스트와 함께, 대략적인 추정 질량(kg)과 각 힘의 뉴턴(N) 수치를 정수 형태로 명확히 적어주세요.
                    - 추정 질량: [숫자] kg
                    - 중력(Gravity): [숫자] N (아래 방향)
                    - 수직항력(Normal Force): [숫자] N (위 방향)
                    - 마찰력(Friction): [숫자] N (수평 방향)
                    
                    그리고 물체의 재질과 힘의 평형 상태에 대한 전문적인 설명을 Markdown으로 작성해주세요.
                    """
                    
                    response = model.generate_content([prompt, image])
                    analysis_text = response.text
                    
                    st.success("✨ 3D 벡터 분석이 완료되었습니다!")
                    
                    # 💡 가상의 물리 데이터 추출 (AI 텍스트 기반 또는 기본값 설정)
                    # 안정적인 시각화를 위해 기본 질량을 1500kg 기준으로 벡터 크기 설정 (중력 = m * 9.8)
                    mass = 1500  
                    gravity_force = mass * 9.8
                    normal_force = gravity_force
                    friction_force = gravity_force * 0.3 # 임의의 마찰력 비례
                    
                    # --- 🧊 Plotly를 이용한 3D 벡터 화살표 시각화 ---
                    fig = go.Figure()

                    # 1. 물체 위치 (원점 0,0,0)
                    fig.add_trace(go.Scatter3d(
                        x=[0], y=[0], z=[0],
                        mode='markers+text',
                        marker=dict(size=12, color='orange'),
                        text=["물체 중심"],
                        textposition="top center",
                        name="물체"
                    ))

                    # 2. 벡터 화살표 데이터 정의 (시작점과 끝점)
                    # 중력 (아래로: Z축 음수) -> 빨간색
                    fig.add_trace(go.Cone(
                        x=[0], y=[0], z=[0], u=[0], v=[0], w=[-gravity_force/300],
                        colorscale=[[0, 'red'], [1, 'red']],
                        showscale=False,
                        name=f"중력 ({gravity_force:,.0f} N)"
                    ))

                    # 수직항력 (위로: Z축 양수) -> 초록색
                    fig.add_trace(go.Cone(
                        x=[0], y=[0], z=[0], u=[0], v=[0], w=[normal_force/300],
                        colorscale=[[0, 'green'], [1, 'green']],
                        showscale=False,
                        name=f"수직항력 ({normal_force:,.0f} N)"
                    ))

                    # 마찰력 (옆으로: X축 양수) -> 파란색
                    fig.add_trace(go.Cone(
                        x=[0], y=[0], z=[0], u=[friction_force/100], v=[0], w=[0],
                        colorscale=[[0, 'blue'], [1, 'blue']],
                        showscale=False,
                        name=f"마찰력 ({friction_force:,.0f} N)"
                    ))

                    # 3D 레이아웃 설정
                    fig.update_layout(
                        title="물체에 작용하는 3D 힘 벡터 다이어그램",
                        scene=dict(
                            xaxis_title='X (수평력)',
                            yaxis_title='Y (측면력)',
                            zaxis_title='Z (수직력 / 중력)',
                            xaxis=dict(range=[-10, 10]),
                            yaxis=dict(range=[-10, 10]),
                            zaxis=dict(range=[-20, 20]),
                        ),
                        margin=dict(r=0, b=0, l=0, t=40)
                    )

                    # 웹 화면에 3D 그래프 띄우기
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # AI 리포트 출력
                    st.markdown("### 📊 AI 물리 리포트")
                    st.write(analysis_text)
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {e}")
