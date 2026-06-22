#!/bin/bash
echo "=== Copying Open Files to '내 지식 쌓이는곳' ==="

# 대상 폴더 정의
TARGET_GLOBAL="/Users/seopro/내 지식 쌓이는곳"
TARGET_LOCAL="/Users/seopro/테스트프로젝트/내 지식 쌓이는곳"

# 폴더 생성 확인
mkdir -p "$TARGET_GLOBAL"
mkdir -p "$TARGET_LOCAL"

# 1. 4강-2.py 복사
if [ -f "/Users/seopro/Downloads/4강-2.py" ]; then
    cp "/Users/seopro/Downloads/4강-2.py" "$TARGET_GLOBAL/"
    cp "/Users/seopro/Downloads/4강-2.py" "$TARGET_LOCAL/"
    echo "✅ 4강-2.py 복사 완료"
else
    echo "❌ 4강-2.py 원본 파일을 찾을 수 없습니다."
fi

# 2. workers.py 복사
if [ -f "/Users/seopro/Desktop/완전자동화/agents/workers.py" ]; then
    cp "/Users/seopro/Desktop/완전자동화/agents/workers.py" "$TARGET_GLOBAL/"
    cp "/Users/seopro/Desktop/완전자동화/agents/workers.py" "$TARGET_LOCAL/"
    echo "✅ workers.py 복사 완료"
else
    echo "❌ workers.py 원본 파일을 찾을 수 없습니다."
fi

# 3. zone_fetch_thread.py 복사
if [ -f "/Users/seopro/Desktop/완전자동화/zone_fetch_thread.py" ]; then
    cp "/Users/seopro/Desktop/완전자동화/zone_fetch_thread.py" "$TARGET_GLOBAL/"
    cp "/Users/seopro/Desktop/완전자동화/zone_fetch_thread.py" "$TARGET_LOCAL/"
    echo "✅ zone_fetch_thread.py 복사 완료"
else
    echo "❌ zone_fetch_thread.py 원본 파일을 찾을 수 없습니다."
fi

# 4. data_parser.py 복사
if [ -f "$TARGET_GLOBAL/테스트프로젝트/테스트프로젝트/backend/data_parser.py" ]; then
    cp "$TARGET_GLOBAL/테스트프로젝트/테스트프로젝트/backend/data_parser.py" "$TARGET_GLOBAL/"
    cp "$TARGET_GLOBAL/테스트프로젝트/테스트프로젝트/backend/data_parser.py" "$TARGET_LOCAL/"
    echo "✅ data_parser.py 복사 완료"
else
    echo "❌ data_parser.py 원본 파일을 찾을 수 없습니다."
fi

echo "=== 복사 완료! ==="
