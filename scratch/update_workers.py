import unicodedata

def update_file(file_path):
    # NFD 정규화 경로 대응
    p = unicodedata.normalize('NFD', file_path)
    try:
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False
    
    target_text = "반드시 34평형(전용 84m²) 매물의 정보를 최우선 적용하고, 실거래가를 말해줄 때는 반드시 몇 평형(전용면적) 기준인지, 어떤 거래 날짜(연월)분인지, 얼마에 실거래되었는지를 같이 구체적으로 명시하십시오 (예: '34평형(전용 84.97m²) 기준 2026년 4월에 34.5억 원에 실거래')."
    replacement_text = "반드시 [10. 국토교통부 실거래가 표 이미지 글자] OCR 결과를 바탕으로 주변 대장 아파트 34평형(전용 84m² 내외)의 실제 최근 실거래가(계약 연월, 거래 금액 등) 정보를 100% 팩트에 기반하여 정확하게 인용하고, 절대로 예시 수치('34.5억')나 임의의 다른 가격을 지어내지 마십시오."
    
    # NFC 정규화 상태에서 replace 시도
    content_nfc = unicodedata.normalize('NFC', content)
    target_nfc = unicodedata.normalize('NFC', target_text)
    replacement_nfc = unicodedata.normalize('NFC', replacement_text)
    
    if target_nfc in content_nfc:
        content_nfc = content_nfc.replace(target_nfc, replacement_nfc)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content_nfc)
        print(f"Success updating {file_path} (NFC)")
        return True
    
    # NFD 상태에서도 시도
    content_nfd = unicodedata.normalize('NFD', content)
    target_nfd = unicodedata.normalize('NFD', target_text)
    replacement_nfd = unicodedata.normalize('NFD', replacement_text)
    
    if target_nfd in content_nfd:
        content_nfd = content_nfd.replace(target_nfd, replacement_nfd)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content_nfd)
        print(f"Success updating {file_path} (NFD)")
        return True
        
    print(f"Target not found in {file_path}")
    return False

# 둘 다 업데이트
update_file('/Users/seopro/Desktop/완전자동화/agents/workers.py')
update_file('/Users/seopro/내 지식 쌓이는곳/테스트프로젝트/agents/workers.py')
