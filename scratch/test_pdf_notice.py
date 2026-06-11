import os
import sys

# Add project path to sys.path
sys.path.append("/Users/seopro/테스트프로젝트")

from utils.hwpx_renderer import capture_url_screenshot, extract_text_from_hwpx

def main():
    url = "https://www.sd.go.kr/main/selectBbsNttView.do?key=1307&bbsNo=166&nttNo=336240&integrDeptCode=30301590000"
    save_path = "/Users/seopro/테스트프로젝트/scratch/gosi/test_geumho16_output.png"
    zone_name = "금호16구역"

    print("=== Testing capture_url_screenshot ===")
    res_path = capture_url_screenshot(url, save_path, zone_name=zone_name)
    print(f"Result Image Path: {res_path}")

    if os.path.exists(save_path):
        print(f"[SUCCESS] Screenshot successfully created at {save_path}")
        # Verify size
        size = os.path.getsize(save_path)
        print(f"Screenshot size: {size} bytes")
    else:
        print("[FAILURE] Screenshot was not created!")

    # Verify backup files exist
    backup_path = "/Users/seopro/테스트프로젝트/scratch/gosi/last_downloaded_gosi.hwpx"
    if os.path.exists(backup_path):
        print(f"[SUCCESS] Backup file saved at {backup_path}")
        # Test text extraction from backup
        text = extract_text_from_hwpx(backup_path)
        print(f"Extracted text length: {len(text)}")
        print("=== Preview of extracted text (first 300 chars) ===")
        print(text[:300])
        print("===================================================")
        if "금호" in text:
            print("[SUCCESS] Found '금호' in extracted text!")
        else:
            print("[WARNING] Did not find '금호' in extracted text!")
    else:
        print("[FAILURE] Backup file does not exist!")

if __name__ == "__main__":
    main()
