import psycopg2
import requests
import time
from datetime import datetime
import os

# 환경 변수 로드 (load_env.sh 실행 필수)
from dotenv import load_dotenv
load_dotenv()

# PostgreSQL 설정
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}

# PayPal API 설정
PAYPAL_API_URL = "https://api.sandbox.paypal.com/v2/transactions"
PAYPAL_AUTH = {
    'Authorization': f"Bearer {os.getenv('PAYPAL_ACCESS_TOKEN')}"
}

def fetch_postgres_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE processed_at > NOW() - INTERVAL '5 minutes'")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] PostgreSQL 연결 실패: {e}")
        return []

def validate_with_paypal(postgres_data):
    for row in postgres_data:
        tx_id = row[2]  # 가정: PostgreSQL의 transaction_id 컬럼 인덱스
        try:
            response = requests.get(f"{PAYPAL_API_URL}/{tx_id}", headers=PAYPAL_AUTH, timeout=5)
            if response.status_code != 200:
                print(f"[ALERT] PayPal 거래 불일치 (ID: {tx_id}) - 상태 코드: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] PayPal API 요청 실패 (ID: {tx_id}): {e}")

def main():
    while True:
        data = fetch_postgres_data()
        if data:
            validate_with_paypal(data)
        time.sleep(10)  # 10초 간격으로 실시간 모니터링

if __name__ == "__main__":
    main()