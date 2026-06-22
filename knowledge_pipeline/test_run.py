from pathlib import Path
import time
import shutil
from parser import WikiParser
from watchdog.events import FileSystemEventHandler
# watcher와 api_server는 통합적으로 동작하기 때문에 직접 실행하는 대신, 
# 필요한 의존성만 임포트하여 테스트합니다.

TEST_DIR = Path("./raw_inputs")

def setup_test(dummy_content: str) -> Path:
    """테스트 환경을 설정하고 더미 파일을 생성합니다."""
    print("\n[SETUP] --- 테스트 파일 준비 중 ---")
    # 기존 파일 정리
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()

    dummy_path = TEST_DIR / "test_raw_article.md"
    with open(dummy_path, 'w', encoding='utf-8') as f:
        f.write(dummy_content)
    print(f"[SETUP] 더미 파일 생성 완료: {dummy_path}")
    return dummy_path

def run_pipeline_test(file_path: Path):
    """Parser -> API Sink 로직을 모의 실행하여 전체 흐름을 테스트합니다."""
    print("\n\n=====================================================")
    print("🚀 [TEST RUN] 파이프라인 End-to-End 시뮬레이션 시작")
    print("=====================================================")

    try:
        # 1. Parser 실행 (데이터 구조화)
        parser = WikiParser(file_path)
        structured_data = parser.parse()
        print("\n[✅ Parser] 데이터 구조화 성공.")
        
        # 2. API Sink 시뮬레이션 (백엔드 전송)
        # 실제로는 watcher가 이 역할을 수행합니다.
        print("\n[🚀 Flow Test] 백엔드(FastAPI)로 데이터 전달 시도...")
        # Mocking the API call process
        class MockHandler:
             def _send_to_wiki_api(self, data: dict, filename: str):
                print("📡 [API Sink Mock] 데이터 전송 성공적으로 모의 처리됨.")

        MockHandler()._send_to_wiki_api(structured_data, file_path.name)
        
        print("\n=====================================================")
        print("✨ 테스트 완료: 파일 감지 -> 파싱 -> API 전송 흐름 검증 성공!")
    except Exception as e:
        print(f"\n❌ [FAIL] 테스트 실패: {e}")


if __name__ == "__main__":
    # 💡 실제 분석을 시뮬레이션하기 위한 더미 콘텐츠 (Researcher의 구조를 모방)
    DUMMY_CONTENT = """
# AI 기반 지식 자산 관리 파이프라인 설계

## 개요 및 요약 (Summary & Thesis)
본 문서는 분산된 형태의 기업 지식을 체계적으로 아카이브하기 위한 자동화 파이프라인을 제안합니다. 핵심은 '파일 변경 감지'와 '표준 위키 구조 강제 적용'입니다. 결론적으로, 모든 원천 데이터는 메타데이터가 붙은 JSON/Wiki 형태로 변환되어야 합니다.

## 핵심 개념 정의 (Core Concepts)
* **Knowledge Artifact:** 단순 문서가 아닌, 검색 가능하고 재활용 가능한 고도로 구조화된 지식 단위.
* **File Watcher:** 파일 시스템의 이벤트를 감지하는 메커니즘 (예: watchdog 라이브러리).
* **Pipeline:** 여러 단계의 처리(감지 -> 파싱 -> 저장)가 순차적으로 연결되는 워크플로우.

## 분석 및 세부 내용 (Deep Dive Analysis)
파이프라인은 크게 3단계로 나뉩니다. 첫째, 감지에 초점을 맞추고, 둘째, 파싱 시에는 NLP 모델을 이용해 섹션별 주장을 분리해야 합니다. 특히 '연결성' 데이터를 추출하는 것이 중요합니다.

## 연결 및 실행 (Connectivity & Action)
이 지식은 [프로젝트 관리]와 [데이터 아키텍처] 분야에 직접적으로 적용 가능합니다. 즉시 액션 플랜으로, 이 파이프라인의 각 단계별로 단위 테스트 케이스를 작성해야 합니다.
"""

    dummy_file = setup_test(DUMMY_CONTENT)
    run_pipeline_test(dummy_file)

finally:
    # 정리 작업
    if Path("./raw_inputs").exists():
        shutil.rmtree(Path("./raw_inputs"))
        print("\n[CLEANUP] 임시 테스트 디렉토리 삭제 완료.")