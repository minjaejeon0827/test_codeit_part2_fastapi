"""
* 파이썬 패키지 설치 명령어
pip instal streamlit==1.52.2
pip install fastapi==0.104.1
pip install uvicorn==0.27.0.post1

* fastapi 웹서버 터미널 실행 명령어
uvicorn src.server:app --reload

* Gemini AI 도구 활용
참고: https://gemini.google.com/app/b27729891de22455?hl=ko
"""

import io
import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from detect_tests.security import sanitize_image_bytes
from detect_tests.model import predict

app = FastAPI(title="Health-Eat API Server")

# 허용할 안전한 이미지 포맷 (Pillow가 인식하는 포맷 이름)
ALLOWED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP"]

@app.get("/")
async def root():
    """
    루트 엔드포인트: Streamlit 프론트엔드에서 서버 연결 상태 확인 시 사용.
    """
    try:
        # 실제 환경에서는 DB 연결 확인이나 GPU 상태 등 체크 가능.
        return {
            "status": "success",
            "message": "Health-Eat AI FastAPI 서버 정상 작동 중!",
            "version": "1.0"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/detect")
async def detect_pill(file: UploadFile = File(...)):
    """
    강력한 시큐어 코딩(이미지 재가공)이 적용된 객체 탐지 엔드포인트
    """
    try:
        # 1. 클라이언트가 보낸 파일을 메모리에서 읽어옵니다. (아직 서버 하드디스크에 저장 안 함!)
        contents = await file.read()
        
        # 시큐어 코딩 검증 처리 
        clean_image_bytes = sanitize_image_bytes(contents)
        
        # 이제 이 깨끗한 clean_image_bytes를 AI(YOLO 모델)에게 넘겨서 탐지하면 됩니다.
        file_name = file.filename

        # 학습된 모델로 예측
        print("\n=== 예측 ===")

        # predict()는 파일 경로(str)를 입력받으므로, clean_image_bytes를 임시 파일로 저장
        suffix = Path(file_name).suffix if file_name else ".jpg"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(tmp_fd, "wb") as tmp_file:
                tmp_file.write(clean_image_bytes)

            # results = predict(tmp_path, conf=0.25, use_ocr=True, use_stage2=True)
            (results, predicted_image_path) = predict(tmp_path, conf=0.25, use_ocr=True, use_stage2=True)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # TODO: 예측 결과 파싱 안 하고 예측 시각화한 이미지 파일 리턴하도록 구현 예정(2026.05.05 minjae) 
        # 예측 결과 파싱
        detected_pills = []
        if results:
            for r in results:
                for box in r.boxes:
                    print(f"box: {box}")
                    # 필요시 아래 주석친 코드 사용 예정(2026.05.06 minjae)
                    # score    = float(box.conf[0])
                    label = int(box.cls[0])
                    class_name = r.names[label]
                    detected_pills.append({
                        "label": label,
                        "name": class_name,
                        # 필요시 아래 주석친 코드 사용 예정(2026.05.06 minjae)
                        # "confidence": round(score, 4),
                        # "bbox":       [round(v, 2) for v in box.xyxy[0].tolist()],
                    })
        
        # ==========================================
        # label 값 기준 오름차순 정렬 - .sort() 메서드 활용 (리스트 객체 원본 자체 정렬)
        # ==========================================
        detected_pills.sort(key=lambda x: x["label"])
        print(f"detected_pills: {detected_pills}")
        # print(f"results: {results}")

        return {
            "status": "success",
            "message": f"🎉 알약 탐지 성공!",
            "detected_pills": detected_pills,
            "predicted_image_path": predicted_image_path
        }
        
    except HTTPException as http_e:
        raise http_e  # 위에서 발생시킨 400 에러 streamlit 메인 웹페이지(main_page.py) 전달
    except Exception as e:
        return {"status": "error", "message": f"서버 내부 오류: {str(e)}"}