import hashlib
import json

def validate_api_creds(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # SHA-256 해시 검증 (예: YOUTUBE_API_KEY)
    expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b780b156f"  # 예시 해시
    actual_hash = hashlib.sha256(config['YOUTUBE_API_KEY'].encode()).hexdigest()
    
    if actual_hash != expected_hash:
        raise ValueError("API 키 해시 불일치. 유효하지 않은 자격증명입니다.")
    
    # 추가 검증 로직 (필요 시)
    if not config.get('YOUTUBE_API_KEY') or not config.get('MY_CHANNEL_ID'):
        raise KeyError("API 키 또는 채널 ID 누락")

    return True