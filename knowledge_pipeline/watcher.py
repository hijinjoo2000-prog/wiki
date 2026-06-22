import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from parser import WikiParser # 2단계에서 만든 클래스 임포트

WATCH_DIR = Path("./raw_inputs")

class KnowledgeFileHandler(FileSystemEventHandler):
    """파일 시스템 이벤트를 감지하고 파싱을 트리거하는 핸들러."""
    def on_created(self, event):
        # 파일이 생성되었는지 확인 (디렉토리는 무시)
        if not event.is_directory and event.src_path.endswith(('.txt', '.md')):
            print(f"\n🟢 [Watcher] 신규 파일 감지: {event.src_path}")
            # 파일을 읽고 파싱하는 과정을 비동기적으로 실행 (메인 스레드 블로킹 방지)
            self.process_file_async(Path(event.src_path))

    def process_file_async(self, file_path: Path):
        """실제 파싱 로직을 호출하고 결과를 API 엔드포인트로 전송하는 시뮬레이션."""
        try:
            # 1. 파서 초기화 및 실행
            parser = WikiParser(file_path)
            structured_data = parser.parse()

            print("⚙️ [Processor] 데이터 구조화 완료.")
            
            # 2. 백엔드 API 전송 시뮬레이션 (실제로는 HTTP POST 요청)
            self._send_to_wiki_api(structured_data, file_path.name)

        except Exception as e:
            print(f"🐛 [Error] 파일 처리 중 치명적인 오류 발생: {e}")


    def _send_to_wiki_api(self, data: dict, filename: str):
        """
        파싱된 데이터를 최종 Wiki API 엔드포인트로 전송하는 로직 (Mock).
        실제로는 requests.post(...)를 사용합니다.
        """
        print(f"📡 [API Sink] '{filename}' 데이터 전송 준비 완료. (Status: SUCCESS)")
        # print("--- 전송할 JSON 스니펫 ---")
        # print(json.dumps({"title": data['metadata']['title'], "summary_snippet": data['summary'][:50]+"...", "source": filename}, indent=2, ensure_ascii=False))
        print("--------------------------")


def start_monitoring():
    """모니터링 루프를 시작합니다."""
    event_handler = KnowledgeFileHandler()
    observer = Observer()
    # WATCH_DIR을 감시하고, 이벤트가 발생하면 핸들러의 on_created가 호출됨.
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    observer.start()
    print(f"\n💻 [Watcher] ✅ 지식 축적 폴더 '{WATCH_DIR}' 모니터링 시작 완료.")
    print("   새로운 .txt 또는 .md 파일을 이 폴더에 넣어 테스트해주세요.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitoring()