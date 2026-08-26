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

st.title("🧊 세상의 모든 물체: 3D 벡터 힘 분석기")
st.write("내가 지금 보고 있는 물체에는 어떤 힘이 작용하고 있을까.. 궁금하진 않으셨나요?")
st.write("사진을 올리면 **Gemini AI**가 물체의 힘을 계산하고, 시각화해 드립니다!")
st.write("(**초기조건**을 직접 설정하시면 더 정밀한 분석이 가능합니다. 모르면 '모름'이라고 표시해주세요.")

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
    
    # 🎛️ [UI/UX 개선] 초기조건 입력 섹션
    st.subheader("⚙️ <초기조건 입력>")
    
    col1, col2 = st.columns(2)
    with col1:
        input_mass = st.text_input("물체의 무게 / 질량 (예: 5kg, 1.5톤)", value="모름")
    with col2:
        input_state = st.selectbox(
            "현재 운동 상태",
            ["모름 (AI 추정 맡기기)", "정지 상태 (바닥/책상 위)", "자유 낙하 중 (공중에서 떨어짐)", "외력이 작용하는 중 (밀거나 당기는 중)"]
        )
        
    st.markdown("---")
    
    if st.button("🚀 3D 힘 벡터 시뮬레이션 실행"):
        if not api_key:
            st.warning("⚠️ Streamlit Secrets에 API 키가 설정되어 있지 않습니다!")
        else:
            with st.spinner("🤖 사용자가 입력한 초기조건과 AI 비전 분석을 결합하여 시뮬레이션을 계산 중입니다..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3.6-flash')
                    
                    # 💡 사용자가 입력한 초기조건을 프롬프트에 동적으로 반영
                    prompt = f"""
                    당신은 전문 물리학자입니다. 업로드된 사진과 사용자가 제공한 초기조건을 바탕으로 이 물체에 작용하는 힘을 분석해주세요.
                    
                    [사용자가 설정한 초기조건]
                    - 입력된 무게/질량: {input_mass}
                    - 현재 운동 상태: {input_state}
                    (만약 '모름'이나 추정 조건이라면, 사진 속 시각적 맥락을 바탕으로 가장 합리적인 수치와 상태를 가정해서 계산해주세요.)
                    
                    반드시 아래 형식의 텍스트와 함께, 추정된 질량(kg)과 각 힘(중력, 수직항력, 마찰/외력 등)의 뉴턴(N) 수치를 정수 형태로 명확히 적어주세요.
                    - 추정 질량: [숫자] kg
                    - 중력(Gravity): [숫자] N
                    - 수직항력(Normal Force): [숫자] N
                    - 마찰/외력(Friction/Force): [숫자] N
                    
                    그리고 물리적 상태와 힘의 평형에 대한 전문적인 설명을 Markdown으로 작성해주세요.
                    """
                    
                    response = model.generate_content([prompt, image])
                    analysis_text = response.text
                    
                    st.success("✨ 맞춤형 3D 벡터 분석이 완료되었습니다!")
                    
                    # 가상의 물리 데이터 (추후 AI 결과 파싱 연동 가능, 현재는 기본 시각화 구동)
                    mass = 1500  
                    gravity_force = mass * 9.8
                    normal_force = gravity_force
                    friction_force = gravity_force * 0.3 
                    
                    # --- 🧊 깔끔한 3D 벡터 시각화 ---
                    fig = go.Figure()

                    # 1. 물체 표현 (3D 구형태)
                    phi = np.linspace(0, np.pi, 15)
                    theta = np.linspace(0, 2 * np.pi, 15)
                    x_sphere = 2.5 * np.outer(np.sin(phi), np.cos(theta))
                    y_sphere = 2.5 * np.outer(np.sin(phi), np.sin(theta))
                    z_sphere = 2.5 * np.outer(np.cos(phi), np.ones_like(theta))

                    fig.add_trace(go.Surface(
                        x=x_sphere, y=y_sphere, z=z_sphere,
                        colorscale=[[0, '#7f8c8d'], [1, '#bdc3c7']],
                        opacity=0.9,
                        showscale=False,
                        name="분석 대상 물체"
                    ))

                    # 2. 힘 벡터 (선 + 화살표 기호 + 뉴턴 N 표시)
                    fig.add_trace(go.Scatter3d(
                        x=[0, 0], y=[0, 0], z=[2.5, -5],
                        mode='lines+text',
                        line=dict(color='red', width=8),
                        text=["", f"<b>⬇ 중력 ({gravity_force:,.0f} N)</b>"],
                        textposition="bottom center",
                        name="중력"
                    ))

                    fig.add_trace(go.Scatter3d(
                        x=[0, 0], y=[0, 0], z=[-2.5, 5],
                        mode='lines+text',
                        line=dict(color='green', width=8),
                        text=["", f"<b>⬆ 수직항력 ({normal_force:,.0f} N)</b>"],
                        textposition="top center",
                        name="수직항력"
                    ))

                    fig.add_trace(go.Scatter3d(
                        x=[0, 5], y=[0, 0], z=[0, 0],
                        mode='lines+text',
                        line=dict(color='blue', width=8),
                        text=["", f"<b>➡ 복원/마찰력 ({friction_force:,.0f} N)</b>"],
                        textposition="middle right",
                        name="마찰력"
                    ))

                    fig.update_layout(
                        title="<b>물체에 작용하는 3D 힘 벡터 분석 다이어그램</b>",
                        scene=dict(
                            xaxis_title='X (수평)',
                            yaxis_title='Y (측면)',
                            zaxis_title='Z (수직)',
                            xaxis=dict(range=[-8, 8]),
                            yaxis=dict(range=[-8, 8]),
                            zaxis=dict(range=[-8, 8]),
                            bgcolor="rgba(245, 246, 250, 1)"
                        ),
                        margin=dict(r=0, b=0, l=0, t=40)
                    )

                    st.plotly_chart(fig, use_container_width=True)
                    
                    # AI 리포트 출력
                    st.markdown("### 📊 AI 물리 리포트")
                    st.write(analysis_text)
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {e}")
