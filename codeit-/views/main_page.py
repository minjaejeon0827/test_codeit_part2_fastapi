"""
streamlit 메인 웹페이지.

* streamlit 메인 웹페이지 -> 서브 웹페이지 이동
참고: https://leemcse.tistory.com/entry/%ED%8E%98%EC%9D%B4%EC%A7%80-%EC%9D%B4%EB%8F%99-main%EA%B3%BC-sub-%ED%8E%98%EC%9D%B4%EC%A7%80-%EC%9D%B4%EB%8F%99

* Gemini AI 도구 활용
참고: https://gemini.google.com/app/b27729891de22455?hl=ko
"""

import json
import streamlit as st
import requests
from pathlib import Path
from fastapi import UploadFile

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSS_FILE_NAME = PROJECT_ROOT / "public" / "css" / "main.css"
FOOTER_BANNER_FILE_NAME = PROJECT_ROOT / "public" / "images" / "footer_banner.png"
RIGHT_BANNER_FILE_NAME = PROJECT_ROOT / "public" / "images" / "right_banner.png"
JSON_FILE_NAME = PROJECT_ROOT / "detect_tests" / "pill_safety_info.json"  # 약 정보 JSON 파일 경로
LOCALHOST = "http://127.0.0.1:8000/"
DETECT_URL = f"{LOCALHOST}detect"

@st.cache_data
def load_pill_safety_info(file_path: str) -> dict:
    """약 정보 JSON 파일을 읽어옵니다. (캐싱 적용)"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"[오류] 약 정보 파일 존재 안 함!: {file_path}")
        return {}

def load_css(file_name: str) -> None:
    """main.css 파일 로드 및 Streamlit 적용"""

    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"[오류] main.css 파일 존재 안 함!: {file_name}")
    
def display_server_connection():
    """FastAPI 서버 연결 상태 확인 및 사이드바 표시."""
    st.sidebar.caption("서버 상태")
    
    try:
        # FastAPI 서버(기본 포트 8000) 루트 엔드포인트("/") Http GET 통신. (안정성을 위해 2초 타임아웃 설정)
        response = requests.get(LOCALHOST, timeout=2)
        if response.status_code == 200:
            st.sidebar.success("🟢 서버 연결됨")
        else:
            st.sidebar.warning("🟡 서버 응답 오류")
            
    # except requests.exceptions.ConnectionError:
    except requests.exceptions.RequestException:
        st.sidebar.error("🔴 서버 꺼져있음")  # ConnectionError뿐만 아니라 Timeout 등 모든 요청 관련 오류 포괄하여 처리
    
def post_detect(uploaded_file: UploadFile, msg_container) -> None:
    # 1. 서버로 보낼 '파일 상자' 만들기
    # (파일 이름, 파일의 실제 데이터, 파일 종류) 순서로 포장.
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        
    try:
        # 2. FastAPI 서버의 /detect 창구로 POST 통신(요청) 쏘기!
        # timeout=10 은 서버가 10초 안에 답이 없으면 포기.
        response = requests.post(DETECT_URL, files=files, timeout=10)
      
        # 아래 주석친 코드 필요시 참고 (2026.05.06 minjae)
        # raise Exception("[테스트] 서버 통신 오류")  # 예외 발생시킴
        # raise requests.exceptions.RequestException("[테스트] 서버 통신 오류")  # 예외 발생시킴

        # 3. 서버 응답 상태 코드 확인(200 OK)
        if response.status_code == 200:
            # 서버가 준 JSON 데이터 파이썬 딕셔너리 변환.
            result = response.json()
            # 전달받은 넓은 공간(msg_container)에 메시지 출력
            msg_container.success(f"{result['message']}")

            if len(result['detected_pills']) > 0:
                # 파이썬 리스트 내포(List Comprehension) 문법을 사용해 이름만 추출
                pill_names = [pill['name'] for pill in result['detected_pills']]
                # 마크다운 글머리 기호('- ')를 붙여서 깔끔한 리스트 형태로 출력.
                formatted_names = '\n- '.join(pill_names)
                msg_container.info(f"💊 탐지한 알약 목록\n- {formatted_names}")
            else:
                msg_container.info("💊 탐지한 알약 없음.")
                
            # ==========================================
            # 탐지 성공: Session State 업데이트
            # ==========================================
            st.session_state['detect_result'] = "success"
            st.session_state['predicted_image_path'] = result['predicted_image_path']
            st.session_state['detected_pills'] = result['detected_pills']
        else:
            # 탐지 실패 (서버 오류 응답): Session State 업데이트
            st.session_state['detect_result'] = "failure"
            st.session_state['detected_pills'] = []
            
            # ==========================================
            # 오류 발생 시 서버가 보낸 진짜 이유(detail) 꺼내 읽기!
            # ==========================================
            try:
                # 서버가 보낸 오류 응답 메시지(JSON) 파이썬 객체 변환.
                error_data = response.json()
                
                # 포장지 안에 'detail'이라는 쪽지가 있으면 읽고, 없으면 기본 메시지 출력
                error_detail = error_data.get("detail", "알 수 없는 에러가 발생했습니다.")
                
                # 우리가 원하던 바로 그 형태의 오류 메시지를 화면에 띄우기
                msg_container.error(f"⚠️ {response.status_code} Bad Request: {error_detail}")
                
            except ValueError:
                # 만약 서버가 치명적으로 고장나서 JSON 포장지조차 못 만들고 죽었을 때를 대비한 안전망
                msg_container.error(f"⚠️ 서버 오류 발생! (상태 코드: {response.status_code})")                   
    
    except requests.exceptions.RequestException as e:
        # 통신 실패: Session State 업데이트
        st.session_state['detect_result'] = "failure"
        st.session_state['detected_pills'] = []
        # 서버가 꺼져있거나 통신이 끊겼을 때 프로그램이 죽지 않게 막아주기.
        msg_container.error(f"🔴 서버 통신 불가. (오류: {e})")
    
def main_page():
    """Streamlit 메인 웹페이지"""
    try:
        # 아래 테스트 오류 코드 필요시 참고 (2025.10.30 minjae)
        # raise Exception('Streamlit 단위 기능 테스트')  # 예외 발생시킴
        print(f"PROJECT_ROOT: {str(PROJECT_ROOT)}")

        print("Streamlit 메인 웹페이지 함수 시작")

        # 1. 페이지 설정 (제목 및 아이콘)
        st.set_page_config(
            page_title="Health-Eat | 알약 탐지 서비스",
            page_icon="💊",
            # layout="centered",
            layout="wide"
        )
        
        # ==========================================
        # 상태 관리 (Session State) 초기화 세팅
        # ==========================================
        # '닫기' 버튼을 눌렀을 때 파일 업로더를 강제로 비우기 위한 고유 키(Key)
        if 'uploader_key' not in st.session_state:
            st.session_state['uploader_key'] = 0
        
        # '탐지' 버튼을 눌렀을 때 메시지를 띄울지 여부를 결정하는 상태 값
        if 'show_detect_msg' not in st.session_state:
            st.session_state['show_detect_msg'] = False
            
        if 'detect_result' not in st.session_state:
            st.session_state['detect_result'] = None  # None(탐지전), "success"(성공), "failure"(실패)
        
        if 'predicted_image_path' not in st.session_state:
            st.session_state['predicted_image_path'] = None
        
        if 'last_uploaded_file' not in st.session_state:
            st.session_state['last_uploaded_file'] = None
            
        if 'detected_pills' not in st.session_state:
            st.session_state['detected_pills'] = []
        
        # 2. 커스텀 CSS (프로토타입 디자인 적용)
        load_css(str(CSS_FILE_NAME))

        # 3. 사이드바 (메뉴 및 서버 연결 상태 확인)
        st.sidebar.title("Menu")
        # menu = st.sidebar.radio("이동", ["🏠 홈", "📜 탐지 기록", "⚙️ 설정"])
        menu = st.sidebar.radio("이동", "🏠 홈")
        st.sidebar.markdown("---")

        display_server_connection()  # FastAPI 서버 통신 확인 로직 함수 호출

        # 4. 헤더 섹션
        # st.title("🍎 Health-Eat")
        st.title("🔍 PILL SIGHT 알약 탐지 프로그램")
        # st.subheader("🔍 PILL SIGHT 알약 탐지 프로그램")
        st.write("YOLO 기반 실시간 알약 탐지 및 분류 시스템 카메라 또는 이미지 입력으로 알약의 종류와 위치를 자동으로 감지하고, 실험별 성능 지표를 체계적으로 추적·비교합니다.")

        # 5. 검색창 섹션
        # st.write("") 
        # search_query = st.text_input("검색어 입력", placeholder="알약 이름을 입력하세요...", label_visibility="collapsed")
        # st.write("")

        # 6. 메인 기능 카드 (2열 레이아웃)
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.markdown("### 💊 알약 탐지")
                st.caption("AI Detection")
                st.write("사진 업로드 시 AI 모델이 알약을 탐지합니다.")
                
                # 버튼 클릭 시 액션 (나중에 FastAPI의 /detect API를 호출하게 됨)
                # if st.button("📷 사진 업로드"):
                #     st.info("알약 탐지 기능을 실행합니다... (API 연동 필요)")
                
                # 버튼 대신 파일 업로더 위젯 사용 (탐색기 열림, 파일 제한)
                uploaded_file = st.file_uploader(
                    "📷 사진 업로드", 
                    type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                    key=f"uploader_{st.session_state['uploader_key']}", # 키를 바꾸면 업로더가 초기화됨
                    label_visibility="collapsed" # 기본 라벨 글씨 숨김
                )

                if uploaded_file is None:
                    # 파일이 없을 때 기본 메시지
                    # st.write("사진 업로드 시 AI 모델이 알약을 탐지합니다.")
                    pass
                else:
                    # ==========================================
                    # 새로운 이미지 파일 업로드 시 이전 탐지 상태 초기화
                    # ==========================================
                    if st.session_state['last_uploaded_file'] != uploaded_file.name:
                        st.session_state['last_uploaded_file'] = uploaded_file.name
                        st.session_state['detect_result'] = None
                        st.session_state['predicted_image_path'] = None
                        st.session_state['detected_pills'] = []
                        
                    # ==========================================
                    # 이미지 파일 업로드 시 업로더 전체 화면 여백 까지 완전히 삭제!
                    # ==========================================
                    st.markdown("""
                        <style>
                        /* 1. 파일 업로더를 감싸는 껍데기 전체를 완전히 삭제하여 빈 간격 제거 */
                        div.element-container:has([data-testid="stFileUploader"]) {
                            display: none !important;
                        }
                        
                        /* 2. 이 스타일 코드를 주입하는 마크다운 자체의 껍데기 여백도 완전 삭제 */
                        div.element-container:has(style) {
                            display: none !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                    # ==========================================
                    
                    msg_container = st.container()  # "탐지", "닫기" 버튼 위에 메시지만을 위한 별도 공간 생성
                    
                    # 아래 주석친 코드 필요 시 참고(2026.05.06 minjae)
                    # btn_col1, btn_col2 = st.columns(2)  # 이미지 있을 때만 "탐지", "닫기" 버튼 활성화
                    
                    # with btn_col1:
                    #     if st.button("탐지", width="stretch"):
                    #         # st.session_state['show_detect_msg'] = True
                    #         with st.spinner("AI가 알약을 꼼꼼히 분석하고 있어요... 🔍"):
                    #             post_detect(uploaded_file, msg_container)
                    
                    # with btn_col2:
                    #     if st.button("닫기", width="stretch"):
                    #         # 닫기 버튼 클릭 시 상태 완벽 초기화(이미지 포함)
                    #         # uploader_key 숫자를 1 올리면, Streamlit은 파일 업로더가 완전히 새로 생긴 줄 알고 안의 파일을 비워버립니다.
                    #         st.session_state['uploader_key'] += 1
                    #         st.session_state['detect_result'] = None
                    #         st.session_state['predicted_image_path'] = None
                    #         st.session_state['last_uploaded_file'] = None
                    #         # st.session_state['show_detect_msg'] = False # 탐지 메시지도 함께 지움
                    #         st.rerun() # 즉시 화면 새로고침
                            
                    # ==========================================
                    # 닫기 동작 깔끔하게 처리할 콜백 함수 정의
                    # ==========================================
                    def reset_state():
                        st.session_state['uploader_key'] += 1
                        st.session_state['detect_result'] = None
                        st.session_state['predicted_image_path'] = None
                        st.session_state['last_uploaded_file'] = None
                        st.session_state['detected_pills'] = []

                    # 버튼들을 담을 '빈 상자(placeholder)' 생성
                    btn_container = st.empty()
                    detect_clicked = False

                    # 상태에 따라 빈 상자 안에 버튼 그리기
                    with btn_container.container():
                        if st.session_state['detect_result'] == 'failure':
                            # 탐지 실패 시: 닫기 버튼 하나만 전체 너비(100%)로 표시
                            st.button("닫기", width="stretch", key="btn_close_fail", on_click=reset_state)
                        else:
                            # 초기 상태 또는 성공 시: 탐지/닫기 두 버튼을 나란히 표시
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                detect_clicked = st.button("탐지", width="stretch")
                            with btn_col2:
                                st.button("닫기", width="stretch", key="btn_close_normal", on_click=reset_state)
                    
                    # 탐지 버튼 클릭 시 실행 로직
                    if detect_clicked:
                        with st.spinner("AI가 알약을 꼼꼼히 분석하고 있어요... 🔍"):
                            post_detect(uploaded_file, msg_container)
                        
                        # 탐지가 실패로 끝나면 즉시 '빈 상자'를 비우고 닫기 버튼 1개만 다시 그리기!
                        if st.session_state['detect_result'] == 'failure':
                            btn_container.empty()
                            with btn_container.container():
                                st.button("닫기", width="stretch", key="btn_close_fail_after", on_click=reset_state)

                    # ==========================================
                    # 3가지 조건에 따른 이미지 출력 로직
                    # ==========================================
                    if st.session_state['detect_result'] == 'success' and st.session_state['predicted_image_path']:
                        # 조건 2: 탐지 성공 시 -> 예측 시각화 이미지 출력
                        st.image(st.session_state['predicted_image_path'], width="stretch")
                        
                    elif st.session_state['detect_result'] == 'failure':
                        # 조건 3: 탐지 실패 시 -> 이미지 화면 출력 안 함 (pass)
                        pass
                        
                    else:
                        # 조건 1: 사진 업로드 성공 (탐지 버튼 누르기 전) -> 원본 이미지 출력
                        st.image(uploaded_file, width="stretch")

                    # 탐지 버튼 클릭 시 메시지 출력
                    # if st.session_state['show_detect_msg']:
                    #     st.info("[안내] 알약 탐지 기능 추후 구현 예정!")

        with col2:
            with st.container(border=True):
                st.markdown("### 📋 주의사항")
                st.caption("Medication Info")
                
                pill_safety_info_data = load_pill_safety_info(str(JSON_FILE_NAME))
                
                if st.session_state['detect_result'] == 'success' and st.session_state['detected_pills']:
                    st.write("알약 복용 시 주의사항 안내.")
                    
                    for pill in st.session_state['detected_pills']:
                        pill_name = pill['name']
                        info = pill_safety_info_data.get(pill_name)
                        
                        with st.expander(f"💊 {pill_name}", expanded=True):
                            if info:
                                st.markdown(f"**🔹 복용방법:** {info.get('복용방법', '정보 없음')}")
                                st.markdown(f"**🔹 주의사항:** {info.get('주의사항', '정보 없음')}")
                                st.markdown(f"**🔹 주요부작용:** {info.get('주요부작용', '정보 없음')}")
                                st.markdown(f"**🔹 금기:** {info.get('금기', '정보 없음')}")
                                st.markdown(f"**🔹 보관:** {info.get('보관', '정보 없음')}")
                                st.markdown(f"**🔹 상호작용:** {info.get('상호작용', '정보 없음')}")
                            else:
                                st.write("해당 약에 대한 주의사항 정보 존재 안 함!")
                else:
                    st.write("탐지한 알약 주의사항 설명.")
                    # st.write("복용 중인 약의 정보 및 스케줄 관리.")
                    # st.info("알약 사진을 업로드하고 '탐지' 버튼을 눌러주세요.")

        # with col3:  # (오른쪽 배너 공간)
        #     # 오른쪽 배너 이미지를 넣습니다.
        #     # width="stretch" 옵션을 넣으면 상단 레이아웃 너비에 맞춰 100% 꽉 차게 확장됩니다.
        #     st.image(str(RIGHT_BANNER_FILE_NAME), width="stretch")
        #     st.write("")  # 아직 이미지가 없다면 빈 공간 두기.
                    
        # st.write("")  # 빈 공간 두기.
        # st.image(str(FOOTER_BANNER_FILE_NAME), width="stretch")

        # 7. 간단한 푸터
        st.markdown("---")
        st.caption("© 2026 Health-Eat. All rights reserved.")
    except Exception as e:
        st.error(f"[오류] 기능 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main_page()