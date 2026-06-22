import os
import sys
# Python 3.14 + protobuf C-extension 호환성 문제(tp_new TypeError) 우회 패치
sys.modules['google._upb._message'] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import time
import datetime
import shutil
from pathlib import Path

# P-Reinforce 모듈 임포트
try:
    from reinforce import reinforce_main, log
except ImportError:
    def log(message):
        print(f"🤖 [Watcher]: {message}")

BASE_DIR = Path(__file__).parent.resolve()
WATCH_DIR = BASE_DIR / "내 지식 쌓이는곳"
RAW_DIR = BASE_DIR / "00_Raw"

def scan_and_process():
    if not WATCH_DIR.exists():
        log(f"⚠️ 감시 대상 폴더가 존재하지 않습니다: {WATCH_DIR}")
        return

    # 감시 대상 폴더의 루트에 있는 파일들만 스캔 (안전성 및 Inbox 컨셉 유지)
    # 하위 디렉토리는 코드, 라이브러리 등이 포함될 수 있어 제외
    files_to_process = []
    for item in WATCH_DIR.iterdir():
        if item.is_file() and not item.name.startswith("."):
            # .txt 및 .md 파일 대상
            if item.suffix.lower() in [".txt", ".md"]:
                files_to_process.append(item)

    if not files_to_process:
        return

    log(f"📂 '내 지식 쌓이는곳'에서 새 파일 {len(files_to_process)}개 발견!")
    today_str = datetime.date.today().isoformat()
    target_raw_dir = RAW_DIR / today_str
    target_raw_dir.mkdir(parents=True, exist_ok=True)

    moved_any = False
    for file_path in files_to_process:
        dest_path = target_raw_dir / file_path.name
        
        # 파일 이름 충돌 방지
        counter = 1
        while dest_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            dest_path = target_raw_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        try:
            # 파일을 00_Raw/YYYY-MM-DD/ 폴더로 이동 (Inbox 처리)
            shutil.move(str(file_path), str(dest_path))
            log(f"🚚 파일 이동 완료: {file_path.name} -> 00_Raw/{today_str}/{dest_path.name}")
            moved_any = True
        except Exception as e:
            log(f"❌ 파일 이동 중 오류 발생 ({file_path.name}): {e}")

    if moved_any:
        log("🔄 지식 구조화 엔진(P-Reinforce)을 트리거합니다...")
        try:
            # reinforce.py의 메인 프로세스 실행 (분류, 마크다운화, 인덱스 갱신, Git 커밋 & Push)
            reinforce_main()
            log("✨ 지식 구조화 및 동기화 작업이 완료되었습니다!")
        except Exception as e:
            log(f"❌ 지식 구조화 실행 중 에러 발생: {e}")

def main():
    log("👀 '내 지식 쌓이는곳' 감시 서비스가 시작되었습니다. (5초 간격 폴링)")
    log(f"📍 감시 폴더: {WATCH_DIR}")
    
    try:
        while True:
            scan_and_process()
            time.sleep(5)
    except KeyboardInterrupt:
        log("👋 감시 서비스를 종료합니다.")

if __name__ == "__main__":
    main()
