import requests

# PayPal API 테스트 (환경 변수로 인증 정보 관리)
url = "https://api.paypal.com/v1/operations"
headers = {
    "Authorization": "Bearer $PAYPAL_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json={"intent": "CAPTURE"})
print("Status Code:", response.status_code)
print("Response Body:", response.json())