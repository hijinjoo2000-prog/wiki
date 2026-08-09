import requests
import json

# PayPal API 테스트 엔드포인트 (예시)
url = "https://api.sandbox.paypal.com/v2/checkout/orders"
headers = {
    "Content-Type": "application/json",
    "Authorization": "A21EL0J..."  # 실 사용 시 엔드포인트에 맞는 토큰 입력
}

payload = {
    "intent": "CAPTURE",
    "purchase_units": [
        {
            "amount": {
                "currency_code": "USD",
                "value": "10.00"
            }
        }
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.status_code)
print(response.json())