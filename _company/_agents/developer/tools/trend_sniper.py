import datetime
import hashlib
import json
import os

# 1. API 자격증명 검증 (SHA-256 해시 검증)
def validate_api_credentials():
    config_path = os.path.expanduser('~/에이전트 학교/_company/youtube_account.json')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"파일 '{config_path}'을 찾을 수 없습니다. YOUTUBE_API_KEY 및 MY_CHANNEL_ID를 입력해주세요.")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # SHA-256 해시 검증 (예: 사전 정의된 기준값과 비교)
    expected_api_key_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b780b156f"  # 예시 해시
    expected_channel_id_hash = "486ea492793812a0b5d0c3f3e94367e38912a851d0c1f0b472563449e083a2d7"  # 예시 해시

    api_key_hash = hashlib.sha256(config['YOUTUBE_API_KEY'].encode()).hexdigest()
    channel_id_hash = hashlib.sha256(config['MY_CHANNEL_ID'].encode()).hexdigest()

    if api_key_hash != expected_api_key_hash or channel_id_hash != expected_channel_id_hash:
        raise ValueError("API 자격증명의 SHA-256 해시가 일치하지 않습니다. 값 확인 필요.")

# 2. datetime.datetime.utcnow() 대체 (Python 3.11+ 호환)
def get_current_utc_time():
    return datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp(), tz=datetime.timezone.utc)

# 3. 메인 실행
if __name__ == "__main__":
    try:
        validate_api_credentials()
        current_time = get_current_utc_time()
        print(f"✅ API 자격증명 검증 완료. 현재 시간: {current_time}")
        # 추가 작업 (예: API 요청)...
    except Exception as e:
        print(f"❌ 오류 발생: {e}")