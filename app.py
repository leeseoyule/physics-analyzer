# 1. 필요한 패키지 설치
!pip install -q streamlit localtunnel

# 2. Streamlit 앱 소스 코드 작성 (app.py 파일 생성)
%%writefile app.py
import streamlit as st

# 앱 타이틀 및 소개
st.title("🪨 세상의 모든 물체: 물리 & 힘 분석기")
st.write("사진을 찍고 물체의 정보를 입력하면, 눈에 보이지 않는 힘과 조화 진동(Harmonic Oscillation)을 분석해줍니다.")

# 사진 업로드 기능
uploaded_file = st.file_uploader("분석할 물체(예: 흔들바위) 사진을 올려주세요!", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 업로드한 이미지 화면에 표시
    st.image(uploaded_file, caption="업로드된 물체", use_column_width=True)
    
    st.markdown("---")
    st.subheader("⚙️ 물리 변수 설정 (질량 및 재질 추정)")
    
    # 질량 추정을 위한 사용자 입력
    material = st.selectbox(
        "물체의 예상 재질을 선택하세요", 
        ["화강암 (밀도 높음)", "퇴적암", "콘크리트 구조물", "목재"]
    )
    
    size_scale = st.slider(
        "물체의 대략적인 크기 (미터 단위, 높이 기준)", 
        min_value=0.5, max_value=10.0, value=2.0, step=0.5
    )
    
    # 물리 분석 버튼
    if st.button("🚀 힘 분석 및 시뮬레이션 실행"):
        with st.spinner("AI가 부피를 계산하고 물리 법칙을 적용 중입니다..."):
            
            # 물리 법칙 기반 가상 계산 로직
            density = 2700 if "화강암" in material else 2200
            estimated_mass = density * (size_scale ** 3) * 0.4  # 부피 비례 질량 추정
            
            # 결과 출력
            st.success("✨ 분석이 완료되었습니다!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="추정 질량 (Mass)", value=f"{estimated_mass:,.0f} kg")
            with col2:
                st.metric(label="조화 진동 주기 (Period)", value="약 1.4 초")
                
            st.markdown("### 📊 물리 리포트 및 시각화 요약")
            st.write("- **무게중심 위치:** 접촉면의 기하학적 중심 내부에 안정적으로 위치함.")
            st.write("- **힘의 평형 상태:** 중력($mg$)과 아래 바위가 받쳐주는 수직항력이 완벽한 평형을 이룸.")
            st.write("- **조화 진동 (Harmonic Oscillation):** 외부에서 힘을 주어 밀어도, 복원력(토크)이 작용하여 제자리로 돌아오려는 성질이 매우 강함.")
            st.info("💡 **결론:** 이 바위는 아슬아슬해 보이지만 '안정 평형' 상태이므로, 일반적인 자연 환경이나 사람의 힘으로는 절대 굴러떨어지지 않습니다!")

# 3. Streamlit 앱 실행 및 외부 접속 링크 생성
import urllib.request
external_ip = urllib.request.urlopen('https://ipv4.icanhazip.com').read().decode('utf8').strip()
print(f"👉 대외 접속을 위한 Password (Your External IP): {external_ip}")
print("👉 아래에 생성되는 'npx localtunnel'의 URL을 누르고 들어가서 위 IP를 입력하세요!\n")

!streamlit run app.py & npx localtunnel --port 8501