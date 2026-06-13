import requests
import json
import time

url = "https://stitch.googleapis.com/mcp"
headers = {
    "X-Goog-Api-Key": "AQ.Ab8RN6IlVsIf0hQnEdf0ltX0MydJR8dpje9eO9mF2q-MiLM5Og",
    "Content-Type": "application/json"
}

# 1. Start generation
prompt = (
    "An ultra-clean property investment data card design for 금호16구역 입주권. "
    "The top header is a deep black bar with white bold Korean text '금호16구역 입주권'. "
    "Below is a vibrant yellow banner with '초기투자금 : 14.32억' in red text. "
    "The middle section is a clean data grid with columns for market price, premium, appraised value, lease, total purchase, and safety margin. "
    "The premium value is 8.0억 and safety margin is 0.0억, 매매가는 14.32억. "
    "In the bottom-left analysis section, add investment notes. "
    "The contact info is '서프로 : 010-1234-5678'."
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
    "id": 3
}

try:
    print("Sending generate_screen_from_text tool call...")
    res = requests.post(url, headers=headers, json=payload, timeout=120)
    print("Status:", res.status_code)
    data = res.json()
    print("Response:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
