import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
WATCHER_SCRIPT = BASE_DIR / "watch_knowledge.py"
PLIST_LABEL = "com.seopro.wikiwatcher"
LAUNCH_AGENTS_DIR = Path(os.path.expanduser("~/Library/LaunchAgents"))
PLIST_PATH = LAUNCH_AGENTS_DIR / f"{PLIST_LABEL}.plist"

# 현재 사용 중인 Python 실행 파일 경로 획득
PYTHON_PATH = sys.executable

def create_plist():
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_PATH}</string>
        <string>{WATCHER_SCRIPT}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{BASE_DIR}</string>
    <key>StandardOutPath</key>
    <string>{BASE_DIR}/20_Meta/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>{BASE_DIR}/20_Meta/watcher_error.log</string>
</dict>
</plist>
"""
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist_content, encoding="utf-8")
    print(f"✅ LaunchAgent 설정 파일 생성 완료: {PLIST_PATH}")

def load_agent():
    # 혹시 이미 실행 중인 경우 언로드 시도
    unload_agent()
    
    try:
        subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
        print("🚀 백그라운드 감시 서비스를 성공적으로 등록하고 실행했습니다!")
        print("💡 이제 '내 지식 쌓이는곳' 폴더에 파일을 넣으면 백그라운드에서 자동으로 감지 및 처리됩니다.")
        print(f"📝 로그 확인: tail -f {BASE_DIR}/20_Meta/watcher.log")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서비스 로드 중 오류 발생: {e}")

def unload_agent():
    if PLIST_PATH.exists():
        try:
            # 에러 출력을 억제하여 이미 언로드된 상태일 때의 경고를 패스
            subprocess.run(["launchctl", "unload", str(PLIST_PATH)], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print("🛑 기존에 등록된 서비스를 정지 및 제거했습니다.")
        except Exception:
            pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        unload_agent()
    else:
        create_plist()
        load_agent()
