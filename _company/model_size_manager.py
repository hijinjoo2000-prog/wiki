import psutil

def check_memory_usage():
    memory = psutil.virtual_memory()
    if memory.percent > 80:
        print("Memory usage high, switching to smaller model...")
        # 모델 크기 조정 로직 추가
    else:
        print("Memory usage normal.")

check_memory_usage()