import requests
import json
import time

url = "https://stitch.googleapis.com/mcp"
headers = {
    "X-Goog-Api-Key": "AQ.Ab8RN6IlVsIf0hQnEdf0ltX0MydJR8dpje9eO9mF2q-MiLM5Og",
    "Content-Type": "application/json"
}

prompt = (
    "An ultra-clean property investment data card design, precisely following the layout of {{DATA:IMAGE:IMAGE_4}}. "
    "The top header is a deep black bar with white bold Korean text \"금호16구역 입주권\". "
    "Below is a vibrant yellow banner with \"초기투자금 : 14.32억\" in bold red text. "
    "The middle section is a clean data grid with columns: 매매가 (14.32억), 프리미엄 (8.0억), "
    "권리가 (6.32억), 임대 (0억), 총 매수가 (14.32억), 안전마진 (0억). "
    "Numeric values for Premium and Safety Margin should be in scarlet red. "
    "The bottom-left analysis section includes 3D glossy blue check marks with investment notes in Korean: "
    "- 진행상황: 관리처분계획인가 완료 및 이주율 95% "
    "- 시공사: 현대건설 디에이치 "
    "- 준공시기: 2029년 하반기 예정 "
    "- 이주비대출: 감정평가액의 60% 무이자 지원 "
    "- 추가분담금 조건: 입주시 100% 납부 조건. "
    "Bottom-right includes \"84m²\" and tax info: \"1.1% (주택)\". "
    "Footer contact info: \"대한민국 재개발 재건축 NO.1 플랫폼 / 서프로 : 010-1234-5678\". "
    "Pure white background, high-fidelity commercial real estate infographic style."
)

payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "generate_screen_from_text",
        "arguments": {
            "projectId": "1517492827801598489",
            "prompt": prompt,
            "designSystem": "assets/0c300160eecb4911bcd33a68bab6176e",
            "deviceType": "DESKTOP",
            "modelId": "GEMINI_3_1_PRO"
        }
    },
    "id": 999
}

try:
    print("Calling generate_screen_from_text...")
    res = requests.post(url, headers=headers, json=payload, timeout=120)
    print("Status:", res.status_code)
    data = res.json()
    print("Full API Response:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
