import os
import unicodedata

# We normalize the path to NFD (Normal Form Decomposition) for Mac OS sandbox permission compatibility.
file_path = unicodedata.normalize('NFD', '/Users/seopro/내 지식 쌓이는곳/테스트프로젝트/agents/workers.py')

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Let's locate the anchors
start_marker = 'ocr_summary_clean = ocr_summary.strip()'
end_marker = 'regulation_report = sub_results[1]'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"Error: Markers not found! Start: {start_idx}, End: {end_idx}")
    exit(1)

# We want to keep everything before `ocr_summary_clean = ocr_summary.strip()` (plus the marker itself and the newline)
before_part = content[:start_idx + len(start_marker)]
after_part = content[end_idx:]

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
            regulation_report = sub_results[1]
            seo_report = sub_results[2]
            
            self.log_signal.emit("✅ [Multi-Agent] 모든 서브 에이전트 분석 완료! 결과를 최종 프롬프트에 결합합니다.\\n")
            
        except Exception as ex:
            self.log_signal.emit(f"❌ [Multi-Agent 에러] 서브 에이전트 가동 실패: {ex}. 기본 처리로 진행합니다.")
            p_rights_val = self.atcl_info.get('p_rights', '-')
            p_premium_val = self.atcl_info.get('p_premium', '-')
            invest_price_val = self.atcl_info.get('invest_price', '-')
            
            financial_report = f\"\"\"## [금융 및 수익성 분석]
금융 분석 에이전트 수행에 일시적 지연이 발생하여, 3단계 OCR 기반 핵심 수치 정보를 포함한 Fail-Safe 테이블을 우선적으로 복구 및 제공합니다:

| 구분 | OCR 및 매물 수치 정보 (금액) |
| --- | --- |
| 감정평가액(권리가액) | {p_rights_val}억 원 |
| 프리미엄 (P) | {p_premium_val}억 원 |
| 초기 실투자금 | {invest_price_val}억 원 |
\"\"\"
            regulation_report = f\"\"\"## [규제 및 법률 검토]
법률 검토 에이전트 수행에 일시적 지연이 발생하여, 기본 가이드라인 및 필수 규제 조항을 안내합니다:
- {target_location}은 투기과열지구(규제지역) 및 토지거래허가구역으로 실거주 의무 및 갭투자 원천 불가능 조건이 적용됩니다.
- 조합원 지위 승계 제한 규정(전매 제한, 예외 요건 포함) 및 5년 재당첨 제한 조항을 반드시 준수하여야 합니다.
- 문의사항은 조합사무실(전화번호: {self.atcl_info.get('phone', '-')})을 이용해 주십시오.
\"\"\"
            seo_report = f\"\"\"## [SEO 최적화]
- [SEO 검색 요약 스니펫 문구]: {target_zone_name} 재개발 매물 분석 브리핑입니다. 프리미엄 {p_premium_val}억 원, 초기투자금 {invest_price_val}억 원으로 진입 가능합니다.
- 해시태그: #{target_keyword} #{area_redev_tag} #{area_name}재개발
\"\"\"

        financial_report_clean = financial_report[:500] if financial_report else ""
        regulation_report_clean = regulation_report[:500] if regulation_report else ""
        seo_report_clean = seo_report[:500] if seo_report else ""

        is_regulated = borough in ["동작구", "용산구", "강남구", "서초구", "송파구", "성동구"]
        if is_regulated:
            regulation_status_text = f"{borough}는 투기과열지구(규제지역)이자 토지거래허가구역으로 묶여 있어 실거주 의무가 부과되며 갭투자가 불가능합니다. 관리처분계획인가 이후에는 조합원 지위 승계 자격 제한이 적용되므로 매수 전에 10년 보유 5년 거주 1주택자 등 예외 허용 기준을 충족하는지 반드시 사전에 확인해야 하며, 5년 재당첨 제한 및 현금청산 리스크도 사전에 검토해야 합니다."
        else:
            regulation_status_text = f"{borough}는 비규제지역으로 투기과열지구 및 토지거래허가구역 규제에서 제외됩니다. 따라서 실거주 의무가 없어 전세를 안고 갭투자를 진행하는 것이 가능하며, 조합원 지위 승계 제한 규정도 투기과열지구에 비해 훨씬 완화되어 있어 거래가 자유롭습니다. 다만, 다주택자 여부에 따른 세금 중과 여부 및 향후 세법 규정은 개별적으로 확인하셔야 합니다."

        base_prompt = f\"\"\"새로운 {target_zone_name} 재개발 매물이 포착되었습니다. 
다음 팩트 데이터와 매물 데이터를 완벽히 인지하여, {"'서프로' 페르소나 블로그 글쓰기 지침에 따라 VVIP 블로그 분석글을 작성하고 최종 저장해 주세요." if self.write_mode == "blog" else "재개발 커뮤니티(네이버 카페) 자유게시판/정보게시판에 적합한 카페 분석글로 작성하고 최종 저장해 주세요."}
전문적이고 신뢰도 높은 분석 톤을 일관되게 유지하십시오.

### [크리티컬 규칙] 투자금 데이터 가공 금지 가중치 적용
- 투자금 데이터(매매가격, 프리미엄, 초기 실투자금 등 모든 수치 데이터) 본문 배치는 가공 금지하며 최신 매물카드 OCR 원본 숫자를 100% 일치시키십시오.


### [중요] 분야별 서브 에이전트 분석 리포트 (필수 인용 및 반영)
최종 집필 시 아래 서브 에이전트들이 분석한 구체적 수치, 금융 시나리오, 법률적 경고 조항, SEO 키워드를 100% 본문에 충실하게 녹여내어 풍부하고 정밀한 본문을 완성하십시오.

[1. 금융 및 수익성 분석 리포트]
{financial_report_clean}

[2. 규제 및 법률 검토 리포트]
{regulation_report_clean}

[3. SEO 최적화 가이드라인]
{seo_report_clean}

### 구역 기본 스펙 (ZONES_DATA)
- 구역: {target_zone_name}
- 위치: {self.atcl_info.get('address', '')}
- 진행현황: {self.atcl_info.get('status_main', '')}
- 세부일정: {self.atcl_info.get('status_sub', '')}
- 총 세대수: {self.atcl_info.get('total_house', '')}
- 조합원 수: {self.atcl_info.get('members', '')}
- 시공사: {self.atcl_info.get('constructor', '')}
- 사업규모: {self.atcl_info.get('scale', '')}
- 준공예상: {self.atcl_info.get('completion', '')}
- 이주비조건: {self.atcl_info.get('move_cost', '')}
- 조합원 비례율: {self.atcl_info.get('rate', '')}
- 조합원분양가: {self.atcl_info.get('member_price', '')}
- 추가분담금: {self.atcl_info.get('contribution', '')}
- 조합전화번호: {self.atcl_info.get('phone', '')}

### 이번 신규 포착 매물 시세 상세
- 매매가격: {self.atcl_info.get('p_sale', '')}억 원
- 프리미엄(P): {self.atcl_info.get('p_premium', '')}억 원
- 초기 실투자금: {self.atcl_info.get('invest_price', '')}억 원
- 권리가격: {self.atcl_info.get('p_rights', '')}억 원
- 임대보증금: {self.atcl_info.get('p_rent', '')}억 원
- 예상 총 매수가격(조합원분양가 포함): {self.atcl_info.get('p_total', '')}억 원
- 예상 안전마진: {self.atcl_info.get('p_margin', '')}억 원
- 예상 취득세: {self.atcl_info.get('final_tax_str', '')}
- 구성타입: {self.atcl_info.get('comp_type', '')}
- 담당 연락처: {self.atcl_info.get('contact', '')}

### 글쓰기 핵심 목표
- 타겟 독자: {area_redev} 매물을 실구매하려는 예비 투자자 타겟
- 타겟 키워드: '{target_keyword}' 키워드가 네이버 노출에 최적화되도록 제목 및 본문에 자연스럽게 포함시키십시오.
- 독자 이탈 방지 및 정독 유도를 위한 필수 반영 내용 (엄격한 본문 레이아웃 및 순서 준수):
  1) **[매물 가격 요약 표]**: 본문 최상단(1행)에 매매가, 프리미엄, 초기투자금, 감정평가액(권리가액), 임대 보증금, 예상 총 매수가격, 예상 안전마진, 예상 취득세율 등을 일목요연하게 정리한 마크다운 표(|---|---|)를 최우선 생성하십시오. 표 위에 제목(##), 인사말, 줄글 소개, 혹은 기호 등 그 어떠한 내용물도 먼저 오게 해서는 안 됩니다. 무조건 마크다운 표가 가장 먼저 와야 채점 점수를 획득할 수 있습니다.
  2) [IMAGE_1] (대표 썸네일 이미지) 배치
  3) ## 🔍 {target_keyword} 사업 개요 및 규제 팩트 체크:
     - 최근 재개발 뉴스를 엮어 서프로 특유의 다정한 첫 인사("우리 프밀리님들!")로 시황 브리핑 전개.
     - 매물의 기본 구역 스펙(진행현황, 세부일정, 세대수, 조합원수, 시공사 등) 정보 서술.
     - [IMAGE_2] (구역별 현황표 이미지) 및 [IMAGE_3] (구역 정보 카드 이미지) 순차 배치.
  4) ## 💰 {target_keyword} 프리미엄 및 초기투자금 상세 분석:
     - [IMAGE_4] (매물 가격 분석 카드 이미지) 배치.
     - 매물 상세 금융 정보 서술 및 예상 안전마진 계산 수치를 **볼드체** 표기. 주변 대장 아파트의 최근 1년 실거래 정보를 전용면적(평형), 거래 연월, 금액을 구체적으로 인용하며 비교. **이번 매물이 34평형(전용 84타입)이므로 실거래가를 인용할 때 반드시 아래 제공된 [10. 국토교통부 실거래가 표 이미지 글자] OCR 결과 텍스트를 직접 한 줄 한 줄 정밀 분석하여, 주변 대장 아파트 34평형(전용 84m² 내외)의 실제 최근 거래 내역(계약 연월, 정확한 거래 금액 등) 정보를 100% 팩트에 기반하여 구체적으로 최소 2건 이상 본문에 직접 텍스트 수치로 인용해서 기술하고 비교 설명하십시오. 절대로 대충 넘어가거나 예시 수치('34.5억')나 가짜 시세를 지어내지 마십시오. 실거래 내역 인용 구문 바로 아래에 [IMAGE_11] (국토교통부 아파트 최신 실거래가 표 이미지)를 배치하여 독자가 실제 거래 내역을 표로 직접 확인할 수 있게 해주십시오.**
     - 추가분담금 총액을 명시한 후 계약금/중도금/잔금 일정 설명. (자금조달모델, 실거래가 밴드 용어 일절 사용 금지)
     - 다주택자 나대지 상태 취득세 4.6% 혜택 및 무주택자 멸실 전 주택 1.1%~3.5% 일반 취득세율 대비에 따른 유불리 차별화 조건 상세 서술.
     - [IMAGE_5] (주소/위치 상세 카드 이미지), [IMAGE_6] (구역 위성/지도 스크린샷 이미지), [IMAGE_7] (구역 배치도/조감도 이미지) 순차 배치.
  5) ## 📍 {target_keyword} 핵심 교통망 및 미래 가치 입지 분석:
     - 여의도/강남 접근성 및 인근 역세권 호재 등 입지 가치 분석.
     - 규제 정보 경고 ({regulation_status_text}).
     - `get_korean_law` 도구를 활용하여 실제 `도시 및 주거환경정비법 제39조` 등 법령 조문을 토시 하나 틀리지 않게 그대로 인용한 뒤.
     - [IMAGE_8] (명함 이미지) 및 [IMAGE_9] (배너 이미지)를 순서대로 연달아 고정 배치.
     - [최하단 해시태그]: 배너 아래 글의 최하단에 `#{target_keyword}`, `#재개발`, `#{area_redev_tag}` 등을 포함하여 **5개에서 8개 사이**의 해시태그를 기입.
- 서프로 페르소나 및 톤앤매너: 10년 차 전문가이자 든든한 멘토 같은 서프로 특유의 정중하고 자신감 넘치는 구어체 톤(예: '~하시죠', '~합니다')과 독자 애칭('우리 프밀리님들!')을 전반에 걸쳐 유기적으로 녹여내어 독자의 신뢰도와 완독률을 대폭 끌어올리십시오.
- 본문 내 적절한 위치에 `[IMAGE_1]` ~ `[IMAGE_11]` 자리 표시자를 위에서 언급한 순서에 맞추어 올바르게 배치하십시오.
- 本文 내에 어떠한 모바일 그림 이모티콘도 절대 쓰지 말고 오직 기호만 사용하세요.
- 글자 수 규정: 원고의 최종 분량은 공백을 포함하여 반드시 **1,800자 이상 2,200자 이하 (2,000자 클래스)** 사이로 매우 풍부하고 길게 작성해야 합니다.
- 본인 소개나 메타적인 설명(예: "안녕하세요", "저장 완료된 리포트입니다")을 절대 적지 말고 오직 본문 텍스트만 출력하십시오.

### [필수 의무 지침: 국토부 실거래가 100% 반영]
- 본문 4번 문단 작성 시, 아래 제공된 [10. 국토교통부 실거래가 표 이미지 글자] OCR 데이터 속 실제 아파트명(예: 신금호파크자이 등), 거래 평형(84m²), 정확한 계약 연월 및 실거래가(억 단위) 정보를 반드시 본문에 텍스트로 적어 설명에 활용하십시오. '이미지 참조' 등으로 얼버무리고 본문에 수치를 적지 않는 것은 규칙 위반입니다.

### [필수 반영] 3단계 핵심 이미지 OCR 데이터 정보
{ocr_summary_clean}
\"\"\"
            financial_report = sub_results[0]
"""

new_content = before_part + replacement_block + after_part

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Replacement done successfully using NFD path normalization!")
