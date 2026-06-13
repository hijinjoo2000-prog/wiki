import os
import unicodedata

src_path = unicodedata.normalize('NFD', '/Users/seopro/내 지식 쌓이는곳/테스트프로젝트/agents/workers.py')
dst_path = '/Users/seopro/.gemini/antigravity-ide/scratch/repaired_workers.py'

with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Locate the anchors
start_marker = 'ocr_summary_clean = ocr_summary.strip()'
end_marker = '            regulation_report = sub_results[1]'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"Error: Markers not found! Start: {start_idx}, End: {end_idx}")
    exit(1)

before_part = content[:start_idx + len(start_marker)]
after_part = content[end_idx:]

# We only replace from the start marker to the end marker.
# Since the end marker is '            regulation_report = sub_results[1]',
# our replacement should end right before regulation_report = sub_results[1].
# This means we just need to provide:
# 1. Variable initialization
# 2. try block up to financial_report = sub_results[0]
replacement_block = """

        # 2. 서브 에이전트 실행 (금융분석, 법률검토, SEO분석)
        make_ui_logger = lambda name: (lambda msg: self.log_signal.emit(f"   [{name}] {msg}"))
        
        financial_report = ""
        regulation_report = ""
        seo_report = ""
        
        try:
            import sub_agents
            self.log_signal.emit("\\n🎙️ [Multi-Agent] 전문 서브 에이전트(금융, 법률, SEO) 순차 분석을 시작합니다...")
            
            financial_task = sub_agents.run_financial_agent(
                self.atcl_info, ocr_summary_clean, 
                log_callback=make_ui_logger("📊 금융분석")
            )
            regulation_task = sub_agents.run_regulation_agent(
                self.atcl_info, 
                log_callback=make_ui_logger("⚖️ 법률검토")
            )
            seo_task = sub_agents.run_seo_agent(
                self.atcl_info, 
                log_callback=make_ui_logger("🔍 SEO분석")
            )
            
            sub_results = await asyncio.gather(financial_task, regulation_task, seo_task)
            
            financial_report = sub_results[0]
"""

new_content = before_part + replacement_block + after_part

# Now, we also want to find 'is_regulated = borough in ["동작구", "용산구", "강남구", "서초구", "송파구"]'
# and replace it with 'is_regulated = borough in ["동작구", "용산구", "강남구", "서초구", "송파구", "성동구"]'
target_reg = 'is_regulated = borough in ["동작구", "용산구", "강남구", "서초구", "송파구"]'
rep_reg = 'is_regulated = borough in ["동작구", "용산구", "강남구", "서초구", "송파구", "성동구"]'

new_content = new_content.replace(target_reg, rep_reg)

with open(dst_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Simplified repaired content generated successfully!")
