import io
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

# 허용할 안전한 이미지 포맷 (Pillow가 인식하는 포맷 이름)
ALLOWED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP"]

def sanitize_image_bytes(contents: bytes) -> bytes:
    """
    이미지 재가공(Re-encoding) 및 파일 끝에 은닉된 악성 스크립트(스텔스 파일) 정화.
    """
    try:
        # 해커가 보낸 파일(곰 인형)을 Pillow 라이브러리 사용해서 열기.
        # (만약 여기서 이미지 파일이 아니라 그냥 악성 스크립트면 바로 에러 발생)
        img = Image.open(io.BytesIO(contents))
            
        # 파일의 진짜 포맷이 우리가 허락한 것(JPEG, PNG 등)인지 확인.
        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise HTTPException(status_code=400, detail=f"위험 감지! 허용되지 않은 포맷({img.format}).")

        # 핵심: 깨끗한 메모리 공간 준비.
        secure_image_io = io.BytesIO()
            
        # 원래 이미지 생김새만 그대로 새 이미지 파일에 다시 그려서(저장해서) 덮어 씌우기
        # 이때 끝에 몰래 붙어있던 악성 스크립트(PHP 등)는 이미지 데이터가 아니기 때문에 전부 버려짐.
        img.save(secure_image_io, format=img.format)
            
        # 이제 불순물이 완벽히 제거된 100% 순수 이미지 데이터만 남음.
        clean_image_bytes = secure_image_io.getvalue()
            
        return clean_image_bytes
            
    except UnidentifiedImageError:
        # 아예 열리지도 않는 가짜 이미지(실행 파일 위장 등) 잡아내기.
        raise HTTPException(status_code=400, detail="위험 감지! 손상되었거나 이미지가 아닌 파일.")
