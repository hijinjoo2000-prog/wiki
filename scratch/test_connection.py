import urllib.request
import urllib.error
import json
import time
import sys

def test_models(base_url, api_key):
    print("1. 로컬 서버 모델 목록 확인 중...")
    req = urllib.request.Request(f"{base_url}/models")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode("utf-8"))
            models = [m["id"] for m in res.get("data", [])]
            print(f"   -> 성공! 사용 가능한 모델 목록: {models}")
            return models
    except Exception as e:
        print(f"   -> 오류 발생: {e}")
        return []

def test_chat(base_url, api_key, model):
    print(f"\n2. '{model}' 모델로 테스트 프롬프트 전송 중...")
    req_data = {
        "model": model,
        "messages": [{"role": "user", "content": "안녕! 너는 누구야? 한 문장으로 답변해줘."}],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(req_data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode("utf-8"))
            latency = time.time() - start_time
            reply = res["choices"][0]["message"]["content"]
            print(f"   -> 성공! (응답 시간: {latency:.2f}초)")
            print(f"\n[로컬 모델 답변]:\n{reply}")
            return True
    except Exception as e:
        print(f"   -> 오류 발생: {e}")
        return False

def main():
    base_url = "http://127.0.0.1:1234/v1"
    api_key = "lm-studio"
    target_model = "google/gemma-4-e4b"
    
    print("=" * 50)
    print("       LM Studio 로컬 LLM 통신 테스트 스크립트")
    print("=" * 50)
    print(f"대상 API: {base_url}")
    print(f"대상 모델: {target_model}\n")
    
    models = test_models(base_url, api_key)
    if target_model in models:
        print(f"   -> 설정한 '{target_model}' 모델이 서버에 활성화되어 있습니다.")
        test_chat(base_url, api_key, target_model)
    elif models:
        print(f"   -> 경고: '{target_model}' 모델이 목록에 없습니다. 대신 첫 번째 모델로 테스트를 진행합니다.")
        test_chat(base_url, api_key, models[0])
    else:
        print("   -> 로컬 서버 연결에 실패했거나 모델이 로드되지 않았습니다. LM Studio가 실행 중인지 확인하세요.")
    print("=" * 50)

if __name__ == "__main__":
    main()
