# -*- coding: utf-8 -*-
import os
import sys

# Add directory to sys.path
sys.path.append("/Users/seopro/Desktop/완전자동화")
sys.path.append("/Users/seopro/Desktop/완전자동화/utils")

from utils.stitch_card_generator import StitchCardGenerator

def run_test():
    # Sample real estate card data
    sample_data = {
        'dist_name': '금호16구역',
        'dist_display': '16구역',
        'prop_type': '입주권',
        'invest_price': '14.32',
        'p_sale': '14.32',
        'p_premium': '8.0',
        'p_rights': '6.32',
        'p_rent': '0',
        'p_total': '14.32',
        'p_margin': '0',
        'final_tax_str': '1.1% (주택)',
        'comp_type': '관리처분계획인가',
        'contact': '서프로 : 010-1234-5678',
        'platform_name': '대한민국 재개발 재건축 NO.1 플랫폼',
        'platform_subtitle': 'NO.1 플랫폼',
        'right_brand_text': '대한민국 재개발 재건축 NO.1 플랫폼',
        'listing_footer': '가장 최신 진행상황은 아래▼ 자세히 나와있습니다.',
        'list_1': '진행상황: 관리처분계획인가 완료 및 이주율 95%',
        'list_2': '시공사: 현대건설 디에이치',
        'list_3': '준공시기: 2029년 하반기 예정',
        'list_4': '이주비대출: 감정평가액의 60% 무이자 지원',
        'list_5': '추가분담금 조건: 입주시 100% 납부 조건'
    }

    # Font path
    font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"

    print("--- STARTING STITCH CARD GENERATION TEST ---")
    try:
        saved_path = StitchCardGenerator.generate_card(sample_data, font_path)
        print("\n--- TEST SUCCESSFUL ---")
        print(f"Generated Card Saved To: {saved_path}")
        if os.path.exists(saved_path):
            print(f"File Size: {os.path.getsize(saved_path)} bytes")
        else:
            print("Warning: File does not exist at return path!")
    except Exception as e:
        print("\n--- TEST FAILED ---")
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
