# -*- coding: utf-8 -*-
import sys
import os

# Python 3.14 + protobuf C-extension 호환성 문제(tp_new TypeError) 우회 패치
sys.modules['google._upb._message'] = None
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import re
import json
import time
import asyncio
import threading
import requests
import urllib
import urllib.parse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from PIL import Image

from PySide6.QtCore import QThread, Signal

# 로컬 설정/안전 모델 가져오기
from config.database import MAIN_AGENT_INSTRUCTIONS, MAIN_AGENT_INSTRUCTIONS_SEO
from config.safe_model import get_safe_sdk_model, get_safe_rest_model

# antigravity SDK 및 seo_tools
from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.hooks import policy
import seo_tools


def parse_relative_date(time_str):
    now = datetime.now()
    if "방금" in time_str or "분 전" in time_str or "시간 전" in time_str:
        return now
    if "어제" in time_str:
        return now - timedelta(days=1)
    if "일 전" in time_str:
        days = int(re.sub(r'[^0-9]', '', time_str) or '0')
        return now - timedelta(days=days)
    m = re.search(r'(\d{4})[./\s]+(\d{1,2})[./\s]+(\d{1,2})', time_str)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return now


def filter_planning_thoughts(text: str) -> str:
    if not text:
        return ""
    import re
    paragraphs = text.split("\n\n")
    cleaned_paragraphs = []
    found_korean_draft = False
    for p in paragraphs:
        if found_korean_draft:
            cleaned_paragraphs.append(p)
        else:
            korean_chars = len(re.findall(r'[\uac00-\ud7a3]', p))
            total_chars = len(re.sub(r'\s+', '', p))
            if total_chars > 0:
                korean_ratio = korean_chars / total_chars
                if (korean_ratio > 0.3 and total_chars > 20) or any(kw in p for kw in ["프밀리님들", "스니펫", "목차"]):
                    found_korean_draft = True
                    cleaned_paragraphs.append(p)
    if not found_korean_draft:
        return ""
    return "\n\n".join(cleaned_paragraphs)


def enforce_rules_in_draft(text, atcl_info):
    if not text:
        return ""
    p_sale = atcl_info.get('p_sale', '-')
    p_premium = atcl_info.get('p_premium', '-')
    invest_price = atcl_info.get('invest_price', '-')
    p_rights = atcl_info.get('p_rights', '-')
    p_rent = atcl_info.get('p_rent', '-')
    p_total = atcl_info.get('p_total', '-')
    p_margin = atcl_info.get('p_margin', '-')
    final_tax_str = atcl_info.get('final_tax_str', '-')
    member_price = atcl_info.get('member_price', '-')
    if not member_price or member_price == '-':
        member_price = '59타입: 8.5억 / 84타입: 10.5억'
    
    forced_table = f"""| 구분 | 상세 내용 |
| --- | --- |
| 매매가격 | {p_sale}억 원 |
| 프리미엄 (P) | {p_premium}억 원 |
| 초기 실투자금 | {invest_price}억 원 |
| 감정평가액 (권리가액) | {p_rights}억 원 |
| 조합원분양가 (조분가) | {member_price} |
| 임대 보증금 | {p_rent}억 원 |
| 예상 총 매수가격 | {p_total}억 원 |
| 예상 안전마진 | **{p_margin}억 원** |
| 예상 취득세 | {final_tax_str} |"""

    # 1. Clear any existing markdown table to avoid duplication
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        s = line.strip()
        if s.startswith('|') or s.endswith('|'):
            continue
        cleaned_lines.append(line)
    clean_text = '\n'.join(cleaned_lines)

    # 2. Count keywords ignoring table strings
    import re
    def count_keyword(kw, txt):
        return len(re.findall(re.escape(kw), txt))
        
    added_desc = ""
    if count_keyword('조합원분양가', clean_text) < 2:
        added_desc += "\n\n본 구역 매수를 고려하실 때 가장 중요한 핵심 지표는 역시 조합원분양가입니다. 인근 시세 대비 조합원분양가 메리트가 매우 높으므로 조합원분양가 수준을 반드시 확인해 보시기 바랍니다."
    if count_keyword('조분가', clean_text) < 2:
        added_desc += "\n\n이러한 낮은 조분가(조합원분양가) 덕분에 총 매수가액이 낮게 억제되어 높은 수익률을 확보할 수 있는 것입니다. 조분가 조건을 필히 주변 아파트와 대조해 보십시오."
    if count_keyword('안전마진', clean_text) < 2:
        added_desc += "\n\n본 매물의 예상 안전마진은 인근 신축 단지 실거래가와 비교해 볼 때 매우 넉넉하며, 이러한 두터운 안전마진 덕분에 확실한 투자 안정성을 보장받게 됩니다."

    if added_desc:
        hashtag_idx = clean_text.rfind('#')
        if hashtag_idx != -1:
            clean_text = clean_text[:hashtag_idx] + added_desc + "\n\n" + clean_text[hashtag_idx:]
        else:
            clean_text += added_desc

    # 3. Locate [IMAGE_4] and insert table right after it; otherwise, insert at the top.
    if '[IMAGE_4]' in clean_text:
        new_text = clean_text.replace('[IMAGE_4]', f'[IMAGE_4]\n\n{forced_table}')
    else:
        new_text = forced_table + "\n\n" + clean_text.lstrip()
        
    return new_text




class HiddenDataTracker:
    FILTER_KEYWORDS = [
        "매매가", "초투", "실투자", "프리미엄", "피", "필요금액",
        "갭투자", "권리가", "감평", "입주권", "분담금"
    ]

    REPRESENTATIVE_BLOGS = {
        "노량진": [
            {"id": "smart_property", "name": "스마트공인중개사"}
        ],
        "한남": []
    }

    def __init__(self, gemini_api_key):
        self.api_key = gemini_api_key
        self.local_ai_failed = False
        self.local_ai_fail_count = 0
        self._genai_client = None
        self.mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Referer": "https://m.search.naver.com/"
        }
        self.pc_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.naver.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self.img_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://m.blog.naver.com/"
        }

    def log_message(self, message):
        try:
            log_path = "/Users/seopro/Desktop/완전자동화/sniper_debug.log"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [Tracker] {message}\n")
        except Exception:
            pass

    def get_genai_client(self):
        if self._genai_client is None:
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                self.log_message(f"[Tracker] Failed to initialize Gemini Client: {e}")
        return self._genai_client

    def track_hidden_data(self, region_name, price_val, base_date_str, agency_name=""):
        def parse_korean_money(money_str):
            val = 0
            s = money_str.replace(" ", "").replace(",", "")
            m_eok = re.search(r'([\d\.]+)억', s)
            if m_eok: val += float(m_eok.group(1)) * 10000
            m_cheon = re.search(r'([\d]+)천', s)
            if m_cheon: val += int(m_cheon.group(1)) * 1000
            m_man = re.search(r'([\d]+)만', s)
            if m_man: val += int(m_man.group(1))
            if val == 0:
                only_digits = re.sub(r'[^\d]', '', s)
                if only_digits: return int(only_digits)
            return int(val)

        def regex_extract_prices(text):
            extracted = {"프리미엄": 0, "초기투자금": 0, "권리가": 0}
            clean_text = text.replace(" ", "").replace(",", "")
            
            # 프리미엄(P) 패턴
            p_patterns = [
                r'프리미엄([\d\.]+)억',
                r'추정P([\d\.]+)억',
                r'피([\d\.]+)억',
                r'\bP([\d\.]+)억'
            ]
            for pat in p_patterns:
                m = re.search(pat, clean_text, re.IGNORECASE)
                if m:
                    extracted["프리미엄"] = int(float(m.group(1)) * 10000)
                    break
            
            # 초기투자금 패턴
            i_patterns = [
                r'초기투자금([\d\.]+)억',
                r'초투([\d\.]+)억',
                r'실투자금([\d\.]+)억',
                r'실투자([\d\.]+)억'
            ]
            for pat in i_patterns:
                m = re.search(pat, clean_text)
                if m:
                    extracted["초기투자금"] = int(float(m.group(1)) * 10000)
                    break
                    
            # 권리가액 & 감정평가액 패턴 (현업 동의어 통합 추출)
            r_patterns = [
                r'권리가액([\d\.]+)억',
                r'권리가([\d\.]+)억',
                r'감정평가액([\d\.]+)억',
                r'감정평가([\d\.]+)억',
                r'감평가액([\d\.]+)억',
                r'감평가([\d\.]+)억',
                r'감평([\d\.]+)억',
                r'종전가액([\d\.]+)억',
                r'종전가([\d\.]+)억'
            ]
            for pat in r_patterns:
                m = re.search(pat, clean_text)
                if m:
                    extracted["권리가"] = int(float(m.group(1)) * 10000)
                    break
                    
            return extracted

        p_int = int(price_val) if str(price_val).isdigit() else parse_korean_money(str(price_val))
        
        price_str = ""
        if p_int > 0:
            eok = p_int // 10000
            man = p_int % 10000
            if man == 0:
                price_str = f"{eok}억"
            else:
                price_str = f"{eok}억{man}만"
        else:
            price_str = str(price_val)

        queries = [
            f"smart_property {region_name} {price_str}",
            f"smart_property {region_name} 매매 {price_str}",
            f"smart_property {region_name}"
        ]
        
        post_blocks = []
        for q in queries:
            search_url = (
                f"https://search.naver.com/search.naver?ssc=tab.blog.all"
                f"&query={urllib.parse.quote(q)}&sm=tab_opt&nso=so%3Add%2Cp%3Aall"
            )
            try:
                res = requests.get(search_url, headers=self.pc_headers, timeout=8)
                soup = BeautifulSoup(res.text, 'html.parser')
                blocks = soup.select('div._fe_view_power_content')
                if blocks:
                    post_blocks = blocks
                    break
            except Exception:
                continue

        if not post_blocks:
            return {"error": "네이버 검색 결과 블록을 찾지 못했습니다."}

        try:
            base_date = datetime.strptime(base_date_str[:10], "%Y-%m-%d")
        except Exception:
            base_date = datetime.now()

        def build_price_variations(price_num):
            if price_num <= 0: return []
            variations = set()
            eok = price_num // 10000
            man = price_num % 10000
            if man == 0:
                variations.update([f"{eok}억", f"{eok}억원"])
            else:
                cheon = man // 1000
                variations.update([
                    f"{eok}억{man}만", f"{eok}억 {man}만",
                    f"{eok}억{man} yard", f"{eok}억 {man}만원",
                    f"{eok}억{man}", f"{eok}억 {man}",
                ])
                if man % 1000 == 0 and cheon > 0:
                    variations.update([
                        f"{eok}억{cheon}천", f"{eok}억 {cheon}천",
                        f"{eok}억{cheon}천만", f"{eok}억 {cheon}천만",
                    ])
                decimal_val = round(price_num / 10000, 2)
                decimal_str = f"{decimal_val:.1f}"
                if not decimal_str.endswith('.0'):
                    variations.add(f"{decimal_val}억")
            return list(variations)

        price_variations = build_price_variations(p_int)
        agency_keyword = agency_name.strip() if agency_name else ""

        # 평형(타입) 정보 감지 키워드 추출
        target_type = None
        for t in ["59", "84", "106", "114", "1+1", "1플러스1", "원플원"]:
            if t in region_name:
                target_type = t
                break

        candidates_scored = []

        for block in post_blocks:
            time_el = block.select_one('span.sds-comps-profile-info-subtext')
            link_el = None
            for a_el in block.select('a[href*="blog.naver.com"]'):
                href = a_el.get('href', '')
                if re.search(r'blog\.naver\.com/[^/]+/\d+', href) or 'logNo=' in href:
                    link_el = a_el
                    break
            if not link_el:
                link_el = block.select_one('a[href*="blog.naver.com"]')

            if not (time_el and link_el):
                continue

            blog_date = parse_relative_date(time_el.text.strip())
            days_diff = abs((base_date - blog_date).days)
            
            # 날짜 제한을 기존 30일에서 90일로 완화 (Hard Cutoff 제거)
            if days_diff > 90:
                continue

            title_el = block.select_one('span.sds-comps-text-type-headline1')
            body_el = block.select_one('span.sds-comps-text-type-body1')
            
            title_text = title_el.text.strip() if title_el else ""
            preview_text = body_el.text.strip() if body_el else ""
            full_preview = f"{title_text} {preview_text}"

            raw_url = link_el.get('href', '')
            m_url = raw_url.replace("https://blog.naver.com/", "https://m.blog.naver.com/")
            if not m_url.startswith("http"):
                continue

            blog_id_match = re.search(r'blog\.naver\.com/([^/]+)', m_url)
            blog_id = blog_id_match.group(1) if blog_id_match else ""
            
            if blog_id != "smart_property":
                continue

            # 1차 매칭 점수 산정
            score = 100  # 기본 점수
            
            # 1) 날짜 기반 소프트 감점
            score -= int(days_diff * 1.0)
            
            # 2) 구역명 매칭
            region_base = region_name.split()[0] if region_name else ""
            if region_base and region_base in title_text:
                score += 50
            elif region_base and region_base[:3] in title_text:
                score += 20
                
            # 3) 가격 표기 매칭
            if price_str in title_text:
                score += 80
            elif any(v in title_text for v in price_variations):
                score += 60
            elif any(v in preview_text for v in price_variations):
                score += 30

            # 4) 평형(타입) 매칭
            if target_type:
                if target_type in title_text or target_type in preview_text:
                    score += 50
                else:
                    # 다른 평형이 제목에 떡하니 기재되어 있으면 감점
                    other_types = [ot for ot in ["59", "84", "106", "114"] if ot != target_type]
                    if any(ot in title_text for ot in other_types):
                        score -= 30

            # 5) 중개업소 상호 매칭
            if agency_keyword and agency_keyword in full_preview:
                score += 150

            # 6) 키워드 매칭
            has_keyword = any(kw in full_preview for kw in self.FILTER_KEYWORDS)
            if has_keyword:
                score += 20

            candidates_scored.append({
                "url": m_url,
                "score": score,
                "title": title_text,
                "has_keyword": has_keyword,
                "preview": full_preview,
                "days_diff": days_diff
            })

        # 점수 순으로 정렬
        candidates_scored.sort(key=lambda x: x["score"], reverse=True)

        if not candidates_scored:
            return {"error": "조건에 맞는 블로그 글을 찾지 못했습니다."}

        self.log_message(f"Candidates scored count: {len(candidates_scored)}")
        
        evaluated_candidates = []
        
        # 상위 최대 3개의 후보를 심층 분석하여 2차 정밀 스코어링 진행
        for candidate in candidates_scored[:3]:
            c_url = candidate["url"]
            self.log_message(f"Deeply evaluating candidate: {c_url} (1st Score: {candidate['score']})")
            
            try:
                b_res = requests.get(c_url, headers=self.mobile_headers, timeout=8)
                b_soup = BeautifulSoup(b_res.text, 'html.parser')
            except Exception as e:
                self.log_message(f"-> Failed to fetch candidate {c_url}: {e}")
                continue

            c_body_container = (
                b_soup.select_one('.se-main-container')
                or b_soup.select_one('#postViewArea')
                or b_soup.select_one('.post-view')
            )
            
            if c_body_container:
                for tag in c_body_container(['script', 'style']):
                    tag.decompose()
                c_body_text = re.sub(r'\s+', ' ', c_body_container.get_text(separator=' ')).strip()
            else:
                c_body_text = ""

            # 1단계: Text LLM Scan
            text_extracted = None
            if c_body_text:
                self.log_message("-> Running fast 1차 Text LLM Scan...")
                text_result = self._extract_with_text_llm(c_body_text, c_url)
                if text_result and not text_result.get("error"):
                    text_extracted = text_result
                    self.log_message(f"-> 1차 Text LLM Scan Result: {text_extracted}")

            accumulated_result = {"프리미엄": 0, "초기투자금": 0, "권리가": 0, "매매가": 0, "source_url": c_url}
            
            if text_extracted:
                for k in ["프리미엄", "초기투자금", "권리가", "매매가"]:
                    val = float(text_extracted.get(k, 0.0) or 0.0)
                    if val > 0.0:
                        accumulated_result[k] = int(val * 10000)

            # 2단계: 정규식 기반 줄글 스캔 보강
            regex_res = regex_extract_prices(c_body_text)
            for k in ["프리미엄", "초기투자금", "권리가"]:
                if regex_res[k] > 0 and accumulated_result[k] == 0:
                    accumulated_result[k] = regex_res[k]
                    self.log_message(f"-> [Regex Match] Extracted {k}: {regex_res[k]/10000.0}억")

            # 3단계: 이미지 OCR 분석 보강
            if any(accumulated_result[k] == 0 for k in ["프리미엄", "초기투자금", "권리가"]):
                img_urls = []
                if c_body_container:
                    img_tags = c_body_container.select('img')
                    for img in img_tags:
                        src = img.get('data-lazy-src') or img.get('data-src') or img.get('src') or ''
                        if src.startswith('http'):
                            src_lower = src.lower()
                            exclude_keywords = [
                                'profile', 'sticker', 'icon', 'emoji', 'stat.naver.com', 'badge', 'buddy',
                                'map', 'staticmap', 'kakaocdn', 'dthumb', 'blogpfthumb', 'postviewarea',
                                '전화연결', '전화_연결', '부동산_정보', '부동산정보', '약도'
                            ]
                            if not any(x in src_lower for x in exclude_keywords):
                                if "mblogthumb-phinf.pstatic.net" in src:
                                    src = re.sub(r'([?&]type=)[^&]+', r'\g<1>w800', src)
                                if src not in img_urls:
                                    img_urls.append(src)

                og_img = b_soup.select_one('meta[property="og:image"]')
                if og_img and og_img.get('content'):
                    og_src = og_img['content']
                    if "mblogthumb-phinf.pstatic.net" in og_src:
                        og_src = re.sub(r'([?&]type=)[^&]+', r'\g<1>w800', og_src)
                    if og_src not in img_urls and not any(x in og_src.lower() for x in ['profile', 'sticker', 'icon', 'emoji']):
                        img_urls.append(og_src)

                self.log_message(f"-> Saved {len(img_urls)} images. Requesting vision on top 3...")
                for idx, img_url in enumerate(img_urls[:3]):
                    try:
                        import base64
                        r = requests.get(img_url, headers=self.img_headers, timeout=8)
                        if r.status_code != 200 or len(r.content) < 3000:
                            continue
                        content_type = r.headers.get('Content-Type', 'image/jpeg')
                        mime = 'image/png' if 'png' in content_type else ('image/gif' if 'gif' in content_type else ('image/webp' if 'webp' in content_type else 'image/jpeg'))
                        img_b64 = base64.b64encode(r.content).decode('utf-8')
                        
                        import time
                        time.sleep(1.5)
                        
                        vision_result = self._extract_with_vision(img_b64, mime, "", c_url)
                        self.log_message(f"-> Image [{idx}] Vision Result: {vision_result}")
                        
                        if vision_result and not vision_result.get("error"):
                            for k in ["프리미엄", "초기투자금", "권리가", "매매가"]:
                                val = float(vision_result.get(k, 0.0) or 0.0)
                                if val > 0.0 and accumulated_result[k] == 0:
                                    accumulated_result[k] = int(val * 10000)
                            if all(accumulated_result[k] > 0 for k in ["프리미엄", "초기투자금", "권리가"]):
                                break
                    except Exception as ve:
                        self.log_message(f"-> Vision Exception: {ve}")

            # 매매가 산출 (블로그 매매가가 없으면 프리미엄 + 권리가로 보완)
            matched_price = accumulated_result.get("매매가", 0)
            if matched_price == 0 and accumulated_result.get("프리미엄", 0) > 0 and accumulated_result.get("권리가", 0) > 0:
                matched_price = accumulated_result["프리미엄"] + accumulated_result["권리가"]
                accumulated_result["매매가"] = matched_price

            # 2차 세부 스코어 계산
            detail_score = candidate["score"]
            
            # 가격 오차 대조 및 가격 앵커링 점수 반영
            if p_int > 0 and matched_price > 0:
                price_diff = abs(p_int - matched_price)
                if price_diff == 0:
                    detail_score += 500  # 완전 일치 앵커링 가점
                    self.log_message("-> [Price Anchor] 100% price match anchor (+500)")
                elif price_diff <= 2000:
                    detail_score += 200  # 오차 2000만 이하
                elif price_diff <= 5000:
                    detail_score += 100  # 오차 5000만 이하
                elif price_diff <= 10000:
                    detail_score -= 100  # 오차 5000만 초과 ~ 1억 이하 (소프트 감점 후 기각 방지)
                else:
                    detail_score -= 1000  # 오차 1억 초과 (매우 높은 확률로 불일치)
            else:
                # 가격이 없으면 매칭 불확실하므로 대폭 감점
                detail_score -= 150

            # 금액 완결성 보너스 점수
            extracted_items_count = sum(1 for k in ["프리미엄", "초기투자금", "권리가"] if accumulated_result[k] > 0)
            detail_score += (extracted_items_count * 30)
            if extracted_items_count == 3:
                detail_score += 50  # 3대 주요수치 완벽 추출 보너스
            
            evaluated_candidates.append({
                "candidate": candidate,
                "result": accumulated_result,
                "total_score": detail_score,
                "extracted_count": extracted_items_count
            })

        # 최종 스코어로 내림차순 정렬
        evaluated_candidates.sort(key=lambda x: x["total_score"], reverse=True)

        if evaluated_candidates:
            best_match = evaluated_candidates[0]
            self.log_message(f"Best match URL: {best_match['result']['source_url']} (Total Score: {best_match['total_score']})")
            
            # 최종 스코어가 기준치 50점 이상이면 매칭 성공 리턴
            if best_match["total_score"] >= 50:
                # 최소 1개라도 데이터가 있을 때 반환
                if any(best_match["result"][k] > 0 for k in ["프리미엄", "초기투자금", "권리가"]):
                    return best_match["result"]
            
            # 50점 미만이지만, 1차 후보군에 올라왔던 가장 유력한 링크가 존재한다면 '확인필요'에 링크 동봉하여 리턴
            best_url = best_match["result"]["source_url"]
            return {"error": "금액 검증 및 매칭 신뢰도 미달 (가장 유사한 블로그 추천)", "source_url": best_url}

        return {"error": "조건에 맞는 블로그 글을 찾지 못했습니다."}

    def _extract_with_vision(self, img_b64, mime, fallback_text, url):
        vision_prompt = (
            "당신은 대한민국 VVIP 재개발 전문 부동산 분석가입니다.\n"
            "첨부된 이미지는 재개발 입주권 매물 카드 또는 블로그 썸네일/현황표 이미지입니다.\n"
            "이미지를 사람의 눈처럼 정밀하게 분석하여 아래 4가지 항목을 추출하세요.\n\n"
            "[추출 항목 및 동의어 규정]\n"
            "1. 프리미엄(P): '피', 'P', '프리미엄', '추정 프리미엄', '추정 P' 등으로 표기된 매물 웃돈 가격\n"
            "2. 초기투자금: '초투', '실투자금', '현금', '초기투자금', '초기투자비용' 등으로 표기된 실인수 필요 자금\n"
            "3. 권리가: '권리가', '권리가액', '감정평가액', '감정평가', '감평가액', '감평가', '감평', '종전가격', '종전가액', '종전가', '종전가격/권리가액' 등으로 표기된 자산 가치 평가 금액 (감정평가액과 권리가액은 100% 동일한 개념이므로 같은 값으로 추출하십시오)\n"
            "4. 매매가: '매매', '매매가', '매매금액', '총매매금액', '매매가격', '매매가액' 등으로 표기된 총 거래금액\n\n"
            "[변환 규칙]\n"
            "- 모든 금액은 소수점이 포함된 '억' 단위 실수(float)로 추출하세요. (예: 17억 6200만 → 17.62, 7억 3800만 → 7.38, 25억 → 25.0, 5000만 → 0.5)\n"
            "- 이미지에서 찾을 수 없는 항목은 0.0으로 처리.\n"
            "- 텍스트 표/표 이미지에서 숫자를 최대한 찾아낼 것.\n\n"
            "반드시 아래 JSON 포맷으로만 응답. 설명·주석 절대 금지.\n"
            '{"프리미엄": 0.0, "초기투자금": 0.0, "권리가": 0.0, "매매가": 0.0}'
        )
        try:
            from PIL import Image
            import io
            import base64

            img_data = base64.b64decode(img_b64)
            img = Image.open(io.BytesIO(img_data))

            model_name = get_safe_sdk_model()
            client = self.get_genai_client()
            if not client:
                raise Exception("Gemini client initialization failed")

            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[img, vision_prompt],
                        config={"temperature": 0.05, "max_output_tokens": 200}
                    )
                    raw = response.text.strip() if response.text else ""
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        parsed["source_url"] = url
                        return parsed
                except Exception as api_err:
                    err_str = str(api_err)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        self.log_message(f"[Tracker] SDK Vision Rate Limit (429) detected. Sleeping 3.5s (Attempt {attempt+1}/2)...")
                        import time
                        time.sleep(3.5)
                        continue
                    else:
                        self.log_message(f"[Tracker] SDK Vision API Error: {api_err}")
                        break
            return {"error": "Vision API 실패: 최대 재시도 초과 또는 API 오류"}
        except Exception as e:
            self.log_message(f"[Tracker] SDK Vision analysis exception: {e}")
            pass

        if fallback_text:
            return self._extract_with_text_llm(fallback_text, url)
        return {"error": "비전 추출 실패"}

    def _extract_with_text_llm(self, text, url):
        trimmed = text[:6000] if len(text) > 6000 else text
        prompt = f"""당신은 대한민국 상위 1% VVIP 재개발 전문 부동산 분석가입니다.
아래 블로그 본문에서 [프리미엄(P), 초기투자금, 권리가, 매매가] 4가지 은닉 데이터를 추출하세요.

[각 항목 안내 및 동의어 규정]
1. 프리미엄(P): '피', 'P', '프리미엄', '추정 프리미엄', '추정 P' 등으로 표기된 매물 웃돈 가격
2. 초기투자금: '초투', '실투자금', '현금', '초기투자금', '초기투자비용' 등으로 표기된 실인수 필요 자금
3. 권리가: '권리가', '권리가액', '감평가', '감정평가액', '종전가격', '종전가액', '종전가', '종전가격/권리가액' 등으로 표기된 자산 가치 평가 금액
4. 매매가: '매매', '매매가', '매매금액', '총매매금액', '매매가격', '매매가액' 등으로 표기된 총 거래금액

모든 금액은 소수점이 포함된 '억' 단위 실수(float)로 추출하세요. (예: 17억 6200만 → 17.62, 7억 3800만 → 7.38, 25억 → 25.0, 5000만 → 0.5)
추출 불가 항목은 0.0.

[블로그 본문]:
{trimmed}

반드시 아래 JSON 포맷으로만 응답. 설명 절대 금지.
{{"프리미엄": 0.0, "초기투자금": 0.0, "권리가": 0.0, "매매가": 0.0}}"""

        if not getattr(self, 'local_ai_failed', False):
            try:
                base_url = "http://127.0.0.1:1234/v1"
                model_req = requests.get(f"{base_url}/models", timeout=5).json()
                active_model = model_req["data"][0]["id"]
                
                headers = {"Content-Type": "application/json"}
                data = {
                    "model": active_model,
                    "messages": [
                        {"role": "system", "content": "You are a professional real estate analyzer. Reply strictly in JSON format without markdown blocks, commentary, or thoughts."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.05,
                    "max_tokens": 500,
                    "stream": False
                }
                res = requests.post(f"{base_url}/chat/completions", headers=headers, json=data, timeout=180)
                if res.status_code == 200:
                    raw_res = res.json()["choices"][0]["message"]["content"]
                    m = re.search(r'\{.*\}', raw_res, re.DOTALL)
                    if m:
                        parsed = json.loads(m.group(0))
                        result_fixed = {}
                        for k in ["프리미엄", "초기투자금", "권리가", "매매가"]:
                            result_fixed[k] = float(parsed.get(k, 0.0) or 0.0)
                        result_fixed["source_url"] = url
                        self.log_message(f"[Tracker] Local LLM Successful Match: {result_fixed}")
                        self.local_ai_fail_count = 0  # Reset fail count on success
                        return result_fixed
            except Exception as local_err:
                self.local_ai_fail_count = getattr(self, 'local_ai_fail_count', 0) + 1
                if self.local_ai_fail_count >= 3:
                    self.local_ai_failed = True
                    self.log_message(f"[Tracker] Local LLM failed 3 consecutive times ({local_err}). Disabling local LLM and falling back to Remote Gemini...")
                else:
                    self.log_message(f"[Tracker] Local LLM attempt failed ({local_err}). Fail count: {self.local_ai_fail_count}/3. Falling back to Remote Gemini for this row...")

        try:
            client = self.get_genai_client()
            if not client:
                raise Exception("Gemini client initialization failed")
            model_name = get_safe_sdk_model()
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"temperature": 0.05, "max_output_tokens": 200}
            )
            raw = response.text.strip() if response.text else ""
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                result_fixed = {}
                for k in ["프리미엄", "초기투자금", "권리가", "매매가"]:
                    result_fixed[k] = float(parsed.get(k, 0.0) or 0.0)
                result_fixed["source_url"] = url
                return result_fixed
        except Exception as e:
            return {"error": f"텍스트 LLM 실패: {e}"}
        return {"error": "LLM JSON 반환 실패"}


class RivalAnalysisWorker(QThread):
    log_signal = Signal(str)
    result_signal = Signal(dict)
    finished_signal = Signal()

    def __init__(self, keyword, my_content):
        super().__init__()
        self.keyword = keyword
        self.my_content = my_content

    def run(self):
        self.log_signal.emit("🌐 [크롤러] 네이버 검색 라이브 웹페이지 연결 시도 중...")
        try:
            res = seo_tools.analyze_rival_competition(self.my_content, self.keyword)
            self.result_signal.emit(res)
            self.log_signal.emit("✅ [분석 완료] 실시간 라이벌 경쟁도 진단이 완료되었습니다!")
        except Exception as e:
            self.log_signal.emit(f"❌ [에러] 분석 수행 실패: {e}")
        self.finished_signal.emit()


class SniperTrackingWorker(QThread):
    # (row, col, value_text, url)
    cell_updated = Signal(int, int, str, str)
    finished_tracking = Signal()

    def __init__(self, items_to_track, gemini_api_key):
        super().__init__()
        self.items_to_track = items_to_track
        self.tracker = HiddenDataTracker(gemini_api_key)
        self.is_running = True

    def log_message(self, message):
        print(f"[SniperTrackingWorker] {message}")

    def run(self):
        def format_eok(val_man):
            if val_man >= 10000:
                val_eok = round(val_man / 10000.0, 1)
                if val_eok.is_integer():
                    return f"{int(val_eok)}억"
                return f"{val_eok}억"
            return f"{val_man}만"

        for row, apt_name, price, reg_date, agency, cols in self.items_to_track:
            if not self.is_running:
                break
                
            for c in cols:
                self.cell_updated.emit(row, c, "분석 중...", "")
                
            try:
                self.log_message(f"Row {row} Tracking Start for: {apt_name}")
                result = self.tracker.track_hidden_data(apt_name, price, reg_date, agency)
                if not self.is_running:
                    break
                    
                if "error" not in result:
                    url = result.get("source_url", "")
                    
                    if 4 in cols and result.get("프리미엄", 0.0) > 0.0:
                        p_val = result["프리미엄"]
                        p_text = format_eok(p_val)
                        self.log_message(f"Row {row} Emit Premium: {p_text}")
                        self.cell_updated.emit(row, 4, p_text, url)
                        
                    if 3 in cols and result.get("초기투자금", 0.0) > 0.0:
                        i_val = result["초기투자금"]
                        i_text = format_eok(i_val)
                        self.log_message(f"Row {row} Emit Investment: {i_text}")
                        self.cell_updated.emit(row, 3, i_text, url)
                        
                    if 5 in cols and result.get("권리가", 0.0) > 0.0:
                        r_val = result["권리가"]
                        r_text = format_eok(r_val)
                        self.log_message(f"Row {row} Emit Rights: {r_text}")
                        self.cell_updated.emit(row, 5, r_text, url)
                else:
                    url = result.get("source_url", "")
                    self.log_message(f"Row {row} matching failed with error: {result.get('error')}. URL: {url}")
                    if url:
                        for c in cols:
                            self.cell_updated.emit(row, c, "확인필요 (링크)", url)
                    else:
                        for c in cols:
                            self.cell_updated.emit(row, c, "확인필요", "")
            except Exception as e:
                import traceback
                self.log_message(f"!!! Error in Row {row} tracking execution: {e}\n{traceback.format_exc()}")
            
            time.sleep(2.0)
            
        self.log_message("=== SniperTrackingWorker Finished ===")
        self.finished_tracking.emit()

    def stop(self):
        self.is_running = False
        self.log_message("Stop signal received")


class AgentPipelineWorker(QThread):
    log_signal = Signal(str)
    draft_ready_signal = Signal(str)
    draft_seo_ready_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, zone_str, atcl_info, write_mode="blog", generated_images=None, feedback_report=None, previous_draft=None, active_tab_idx=0, draft_type="both"):
        super().__init__()
        self.zone_str = zone_str
        self.atcl_info = atcl_info
        self.write_mode = write_mode
        self.generated_images = generated_images or [""] * 12
        self.feedback_report = feedback_report
        self.previous_draft = previous_draft
        self.active_tab_idx = active_tab_idx
        self.draft_type = draft_type

    def run(self):
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        executor = ThreadPoolExecutor()
        loop.set_default_executor(executor)
        try:
            loop.run_until_complete(self.run_pipeline())
        finally:
            executor.shutdown(wait=False)
            loop.close()

    async def run_pipeline(self):
        # 2. 레거시 데이터 캐시 찌꺼기 즉시 폐기
        seo_tools.LAST_SAVED_POST_CONTENT = None
        seo_tools.LAST_SAVED_POST_PATH = None
        self.log_signal.emit("🧹 [메모리 비우기] 이전 원고 작성에 사용된 레거시 데이터 캐시 찌꺼기를 전면 폐기하고 메모리를 강제 초기화했습니다.")

        # 1. OCR 데이터 추출 및 변수 바인딩 1순위 강제
        # 최신 매물카드 이미지(index 3)와 구역스펙카드(index 2)를 가장 먼저 완벽하게 스캔하도록 프로세스 순서 강제
        self.log_signal.emit("📝 [Copywriter] AI 에이전트 시스템 가동 중...")
        self.log_signal.emit("📸 [OCR Prerequisite] 최신 매물카드 및 구역스펙 스냅샷 이미지 선행 OCR 스캔 시작...")

        async def scan_image_ocr(idx, image_path):
            if not image_path or not os.path.exists(image_path):
                self.log_signal.emit(f"   └─ ⚠️ [선행 OCR 스킵] 이미지 {idx}번 경로가 없거나 존재하지 않습니다.")
                return ""
            
            # 1순위: 로컬 Tesseract OCR 시도
            try:
                import asyncio
                tess_path = "/opt/homebrew/bin/tesseract"
                if not os.path.exists(tess_path):
                    tess_path = "tesseract"
                
                proc = await asyncio.create_subprocess_exec(
                    tess_path, image_path, "stdout", "-l", "kor+eng",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    txt = stdout.decode("utf-8", errors="ignore").strip()
                    if txt:
                        self.log_signal.emit(f"   └─ 📸 [선행 로컬 OCR 완료] 이미지 {idx}번 로컬 Tesseract 분석 성공 ({len(txt)}자 추출)")
                        return txt
                    else:
                        raise RuntimeError("Tesseract returned empty text")
                else:
                    raise RuntimeError(f"Tesseract exit code {proc.returncode}: {stderr.decode('utf-8', errors='ignore')}")
            except Exception as t_err:
                self.log_signal.emit(f"   └─ ⚠️ [선행 로컬 OCR 실패] {t_err}. 2순위 원격 Gemini Vision API로 Fallback 시도...")
                
            # 2순위: 원격 Gemini Vision API
            try:
                if getattr(seo_tools, "_GEMINI_API_EXHAUSTED", False):
                    raise RuntimeError("Gemini API is marked as exhausted globally")
                from google import genai
                model_name = get_safe_sdk_model()
                client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"), http_options={'timeout': 180})
                img = Image.open(image_path)
                
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=[img, "이 이미지 안에 적힌 모든 글자를 텍스트로 정확히 읽어내어 출력해 주세요. 부연설명 없이 오직 추출된 텍스트만 원본 구조(줄바꿈 등)를 최대한 살려서 한국어로 출력하세요."]
                )
                txt = response.text.strip() if response.text else ""
                if txt:
                    self.log_signal.emit(f"   └─ 📸 [선행 OCR 완료] 이미지 {idx}번 분석 성공 ({len(txt)}자 추출)")
                    return txt
                else:
                    raise RuntimeError("Gemini Vision returned empty text")
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "depleted" in err_str or "exhausted" in err_str or "prepayment" in err_str:
                    seo_tools._GEMINI_API_EXHAUSTED = True
                self.log_signal.emit(f"   └─ ❌ [선행 OCR 최종 에러] 이미지 {idx}번 분석 실패: {e}")
                return ""

        img3_path = self.generated_images[3] if 3 < len(self.generated_images) else ""
        img2_path = self.generated_images[2] if 2 < len(self.generated_images) else ""
        
        # Concurrently perform 선행 OCR to optimize performance
        ocr_res_2, ocr_res_3 = await asyncio.gather(
            scan_image_ocr(2, img2_path),
            scan_image_ocr(3, img3_path)
        )
        
        ocr_cached_results = {2: ocr_res_2, 3: ocr_res_3}

        # Parsing extracted values from listing card (index 3)
        ocr_values = {}
        if ocr_res_3:
            def extract_value_after_label(text, label_pattern):
                match = re.search(label_pattern, text, re.IGNORECASE)
                if match:
                    start_idx = match.end()
                    num_match = re.search(r'([\d\.]+)', text[start_idx:start_idx+30])
                    if num_match:
                        return num_match.group(1)
                return None

            normalized = re.sub(r'\s+', ' ', ocr_res_3)
            
            labels = {
                'invest_price': r'초\s*기\s*(?:실\s*)?투\s*자\s*금',
                'p_sale': r'매\s*매\s*가(?:격)?',
                'p_premium': r'프\s*리\s*미\s*엄(?:\s*\(?\s*P\s*\)?|\s*격)?',
                'p_rights': r'권\s*리\s*가(?:격)?',
                'p_rent': r'임\s*대(?:보\s*증\s*금)?',
                'p_total': r'(?:예\s*상\s*)?총\s*매\s*수\s*가(?:격)?',
                'p_margin': r'(?:예\s*상\s*)?안\s*전\s*마\s*진'
            }
            
            for key, pattern in labels.items():
                val = extract_value_after_label(ocr_res_3, pattern)
                if val:
                    ocr_values[key] = val
            
            # Row-by-row table layout fallback
            needed_keys = ['p_sale', 'p_premium', 'p_rights', 'p_rent', 'p_total', 'p_margin']
            if any(k not in ocr_values for k in needed_keys):
                table_pattern = r'매\s*매\s*가\s*프\s*리\s*미\s*엄\s*권\s*리\s*가\s*임\s*대\s*(?:총\s*매\s*수\s*가|예\s*상\s*총\s*매\s*수\s*가)\s*(?:안\s*전\s*마\s*진|예\s*상\s*안\s*전\s*마\s*진)'
                match = re.search(table_pattern, normalized)
                if match:
                    start_idx = match.end()
                    nums = re.findall(r'([\d\.]+)\s*억?', normalized[start_idx:start_idx+150])
                    if len(nums) >= 6:
                        for idx, key in enumerate(needed_keys):
                            if key not in ocr_values:
                                ocr_values[key] = nums[idx]
                                
            # Final fallback for invest_price
            if 'invest_price' not in ocr_values or not ocr_values['invest_price'] or ocr_values['invest_price'] in ['-', '확인필요', '0', '0.0']:
                m = re.search(r'초\s*기\s*(?:실\s*)?투\s*자\s*금\D*([\d\.]+)', normalized)
                if m:
                    ocr_values['invest_price'] = m.group(1)
                else:
                    # Fallback to p_sale if available
                    p_sale_val = ocr_values.get('p_sale') or self.atcl_info.get('p_sale')
                    if p_sale_val and p_sale_val not in ['-', '확인필요', '0', '0.0']:
                        ocr_values['invest_price'] = p_sale_val

        # Override self.atcl_info values with OCR extracted values (1순위 강제 적용)
        if ocr_values:
            self.log_signal.emit(f"📢 [OCR 바인딩] 이미지 분석을 통해 최신 매물 가격 데이터를 바인딩합니다: {ocr_values}")
            for key, val in ocr_values.items():
                if val:
                    self.atcl_info[key] = val
        else:
            self.log_signal.emit("⚠️ [OCR 바인딩 경고] 최신 매물카드 이미지 OCR 스캔에서 가격 데이터를 추출하지 못했습니다. 기존 데이터 또는 UI 입력값을 사용합니다.")

        clean_zone = self.zone_str.replace("구역", "").strip()
        address = self.atcl_info.get('address', '')
        borough = ""
        neighborhood = ""
        m_addr = re.search(r'([가-힇]+구)\s+([가-힇\d]+동)', address)
        if m_addr:
            borough = m_addr.group(1)
            neighborhood = m_addr.group(2)
        else:
            if "노량진" in clean_zone or "대방" in clean_zone or "흑석" in clean_zone:
                borough = "동작구"
                if "대방" in clean_zone:
                    neighborhood = "대방동"
                elif "흑석" in clean_zone:
                    neighborhood = "흑석동"
                else:
                    neighborhood = "노량진동"
            elif "북아현" in clean_zone:
                borough = "서대문구"
                neighborhood = "북아현동"
            elif "신림" in clean_zone:
                borough = "관악구"
                neighborhood = "신림동"
            elif "봉천" in clean_zone:
                borough = "관악구"
                neighborhood = "봉천동"
            elif "금호" in clean_zone:
                borough = "성동구"
                neighborhood = "금호동"
            elif "한남" in clean_zone:
                borough = "용산구"
                neighborhood = "한남동"
            elif "성수" in clean_zone:
                borough = "성동구"
                neighborhood = "성수동"
            elif "수색" in clean_zone:
                borough = "은평구"
                neighborhood = "수색동"
            elif "증산" in clean_zone:
                borough = "은평구"
                neighborhood = "증산동"
            elif "마천" in clean_zone:
                borough = "송파구"
                neighborhood = "마천동"
            elif "거여" in clean_zone:
                borough = "송파구"
                neighborhood = "거여동"
            elif "장위" in clean_zone:
                borough = "성북구"
                neighborhood = "장위동"
            elif "이문" in clean_zone:
                borough = "동대문구"
                neighborhood = "이문동"
            else:
                borough = "동작구"
                neighborhood = "노량진동"

        dynamic_instructions = MAIN_AGENT_INSTRUCTIONS.replace("동작구 노량진동", f"{borough} {neighborhood}").replace("동작구", borough)
        dynamic_instructions_seo = MAIN_AGENT_INSTRUCTIONS_SEO.replace("동작구 노량진동", f"{borough} {neighborhood}").replace("동작구", borough)

        m_zone = re.match(r'^([^\d]+)(\d+)', clean_zone)
        if m_zone:
            area_name = m_zone.group(1).strip()
            zone_num = m_zone.group(2).strip()
        else:
            area_name = clean_zone
            zone_num = ""

        target_zone_name = f"{area_name} {zone_num}구역" if zone_num else area_name
        target_keyword = f"{area_name}{zone_num}구역매물" if zone_num else f"{area_name}매물"
        target_location = f"{borough} {neighborhood}"
        area_redev = f"{area_name}뉴타운" if "노량진" in area_name or "한남" in area_name or "신림" in area_name or "북아현" in area_name or "흑석" in area_name or "수색" in area_name or "금호" in area_name or "성수" in area_name or "장위" in area_name else f"{area_name} 재개발"
        area_redev_tag = f"{area_name}뉴타운" if "노량진" in area_name or "한남" in area_name or "신림" in area_name or "북아현" in area_name or "흑석" in area_name or "수색" in area_name or "금호" in area_name or "성수" in area_name or "장위" in area_name else f"{area_name}재개발"
        
        prefix_map = {
            "노량진": "noryangjin",
            "흑석": "heukseok",
            "한남": "hannam",
            "신림": "shinlim",
            "이문": "imun",
            "갈현": "galhyeon",
            "성수": "seongsu",
            "북아현": "bugahyeon",
            "봉천": "bongcheon",
            "금호": "geumho",
            "수색": "susaek",
            "증산": "jeungsan",
            "마천": "macheon",
            "거여": "geoyeo",
            "장위": "jangwi"
        }
        filename_prefix = prefix_map.get(area_name, "zone")
        filename_normal = f"{filename_prefix}{zone_num}-84.md" if zone_num else f"{filename_prefix}-84.md"
        filename_seo = f"{filename_prefix}{zone_num}-84-seo.md" if zone_num else f"{filename_prefix}-84-seo.md"

        self.log_signal.emit("📝 [Copywriter] AI 에이전트 시스템 가동 중...")
        self.log_signal.emit("🖼️ [OCR] 3단계 생성 이미지(대표 썸네일, 구역현황표, 구역스펙카드, 매물가격카드) 텍스트 분석 시작...")
        
        async def perform_ocr_async(idx, image_path):
            if idx in ocr_cached_results and ocr_cached_results[idx]:
                self.log_signal.emit(f"   └─ 🖼️ [OCR 캐시 사용] 이미지 {idx}번 선행 OCR 결과 재사용")
                return ocr_cached_results[idx]

            if not image_path or not os.path.exists(image_path):
                self.log_signal.emit(f"   └─ ⚠️ [OCR 스킵] 이미지 {idx}번이 생성되지 않았습니다.")
                return f"[이미지 {idx}번 미생성]"

            
            # 1순위: 로컬 Tesseract OCR 시도
            try:
                import asyncio
                tess_path = "/opt/homebrew/bin/tesseract"
                if not os.path.exists(tess_path):
                    tess_path = "tesseract"
                
                proc = await asyncio.create_subprocess_exec(
                    tess_path, image_path, "stdout", "-l", "kor+eng",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    txt = stdout.decode("utf-8", errors="ignore").strip()
                    if txt:
                        self.log_signal.emit(f"   └─ 🖼️ [로컬 OCR 완료] 이미지 {idx}번 로컬 Tesseract 분석 성공 ({len(txt)}자 추출)")
                        return txt
                    else:
                        raise RuntimeError("Tesseract returned empty text")
                else:
                    raise RuntimeError(f"Tesseract exit code {proc.returncode}: {stderr.decode('utf-8', errors='ignore')}")
            except Exception as t_err:
                self.log_signal.emit(f"   └─ ⚠️ [로컬 OCR 실패] {t_err}. 2순위 원격 Gemini Vision API로 Fallback 시도...")
                
            # 2순위: 원격 Gemini Vision API
            try:
                if getattr(seo_tools, "_GEMINI_API_EXHAUSTED", False):
                    raise RuntimeError("Gemini API is marked as exhausted globally")
                from google import genai
                # dynamic model selection 적용
                model_name = get_safe_sdk_model()
                client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"), http_options={'timeout': 180})
                img = Image.open(image_path)
                
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=[img, "이 이미지 안에 적힌 모든 글자를 텍스트로 정확히 읽어내어 출력해 주세요. 부연설명 없이 오직 추출된 텍스트만 원본 구조(줄바꿈 등)를 최대한 살려서 한국어로 출력하세요."]
                )
                txt = response.text.strip() if response.text else ""
                if txt:
                    self.log_signal.emit(f"   └─ 🖼️ [OCR 완료] 이미지 {idx}번 분석 성공 ({len(txt)}자 추출)")
                    return txt
                else:
                    raise RuntimeError("Gemini Vision returned empty text")
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "depleted" in err_str or "exhausted" in err_str or "prepayment" in err_str:
                    seo_tools._GEMINI_API_EXHAUSTED = True
                err_msg = f"[이미지 {idx}번 OCR 추출 실패: 로컬 Tesseract 및 원격 API 모두 실패: {e}]"
                self.log_signal.emit(f"   └─ ❌ [OCR 최종 에러] 이미지 {idx}번 분석 실패: {e}")
                return err_msg

        ocr_tasks = []
        target_indices = [0, 1, 2, 3, 10]
        for idx in target_indices:
            img_path = self.generated_images[idx] if idx < len(self.generated_images) else ""
            ocr_tasks.append(perform_ocr_async(idx, img_path))
        
        ocr_results_raw = await asyncio.gather(*ocr_tasks)
        ocr_results_dict = {idx: ocr_results_raw[i] for i, idx in enumerate(target_indices)}
        self.log_signal.emit("📢 [OCR 완료] 모든 이미지 OCR 분석이 성공적으로 완료되었습니다. 프롬프트에 병합 중...")

        # 1. OCR 결과 정리 (f-string)
        ocr_summary = f"""### 3단계 핵심 이미지 OCR 데이터 정보 (필수 서술 반영)
[0. 대표 썸네일 이미지 글자]
{ocr_results_dict.get(0, '[이미지 0번 미생성]')}

[1. 구역현황표 이미지 글자]
{ocr_results_dict.get(1, '[이미지 1번 미생성]')}

[2. 구역 스펙 요약 카드 이미지 글자]
{ocr_results_dict.get(2, '[이미지 2번 미생성]')}

[3. 매물가격 카드 이미지 글자]
{ocr_results_dict.get(3, '[이미지 3번 미생성]')}

[10. 국토교통부 실거래가 표 이미지 글자]
{ocr_results_dict.get(10, '[이미지 10번 미생성]')}
"""
        ocr_summary_clean = ocr_summary.strip()

        # 2. 서브 에이전트 실행 (금융분석, 법률검토, SEO분석)
        make_ui_logger = lambda name: (lambda msg: self.log_signal.emit(f"   [{name}] {msg}"))
        
        financial_report = ""
        regulation_report = ""
        seo_report = ""
        
        try:
            import sub_agents
            self.log_signal.emit("\n🎙️ [Multi-Agent] 전문 서브 에이전트(금융, 법률, SEO) 순차 분석을 시작합니다...")
            
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
            
            self.log_signal.emit("✅ [Multi-Agent] 모든 서브 에이전트 분석 완료! 결과를 최종 프롬프트에 결합합니다.\n")
            
        except Exception as ex:
            self.log_signal.emit(f"❌ [Multi-Agent 에러] 서브 에이전트 가동 실패: {ex}. 기본 처리로 진행합니다.")
            p_rights_val = self.atcl_info.get('p_rights', '-')
            p_premium_val = self.atcl_info.get('p_premium', '-')
            invest_price_val = self.atcl_info.get('invest_price', '-')
            
            financial_report = f"""## [금융 및 수익성 분석]
금융 분석 에이전트 수행에 일시적 지연이 발생하여, 3단계 OCR 기반 핵심 수치 정보를 포함한 Fail-Safe 테이블을 우선적으로 복구 및 제공합니다:

| 구분 | OCR 및 매물 수치 정보 (금액) |
| --- | --- |
| 감정평가액(권리가액) | {p_rights_val}억 원 |
| 프리미엄 (P) | {p_premium_val}억 원 |
| 초기 실투자금 | {invest_price_val}억 원 |
"""
            regulation_report = f"""## [규제 및 법률 검토]
법률 검토 에이전트 수행에 일시적 지연이 발생하여, 기본 가이드라인 및 필수 규제 조항을 안내합니다:
- {target_location}은 투기과열지구(규제지역) 및 토지거래허가구역으로 실거주 의무 및 갭투자 원천 불가능 조건이 적용됩니다.
- 조합원 지위 승계 제한 규정(전매 제한, 예외 요건 포함) 및 5년 재당첨 제한 조항을 반드시 준수하여야 합니다.
- 문의사항은 조합사무실(전화번호: {self.atcl_info.get('phone', '-')})을 이용해 주십시오.
"""
            seo_report = f"""## [SEO 최적화]
- [SEO 검색 요약 스니펫 문구]: {target_zone_name} 재개발 매물 분석 브리핑입니다. 프리미엄 {p_premium_val}억 원, 초기투자금 {invest_price_val}억 원으로 진입 가능합니다.
- 해시태그: #{target_keyword} #{area_redev_tag} #{area_name}재개발
"""

        financial_report_clean = financial_report[:500] if financial_report else ""
        regulation_report_clean = regulation_report[:500] if regulation_report else ""
        seo_report_clean = seo_report[:500] if seo_report else ""

        is_regulated = borough in ["동작구", "용산구", "강남구", "서초구", "송파구", "성동구"]
        if is_regulated:
            regulation_status_text = f"{borough}는 투기과열지구(규제지역)이자 토지거래허가구역으로 묶여 있어 실거주 의무가 부과되며 갭투자가 불가능합니다. 관리처분계획인가 이후에는 조합원 지위 승계 자격 제한이 적용되므로 매수 전에 10년 보유 5년 거주 1주택자 등 예외 허용 기준을 충족하는지 반드시 사전에 확인해야 하며, 5년 재당첨 제한 및 현금청산 리스크도 사전에 검토해야 합니다."
        else:
            regulation_status_text = f"{borough}는 비규제지역으로 투기과열지구 및 토지거래허가구역 규제에서 제외됩니다. 따라서 실거주 의무가 없어 전세를 안고 갭투자를 진행하는 것이 가능하며, 조합원 지위 승계 제한 규정도 투기과열지구에 비해 훨씬 완화되어 있어 거래가 자유롭습니다. 다만, 다주택자 여부에 따른 세금 중과 여부 및 향후 세법 규정은 개별적으로 확인하셔야 합니다."

        base_prompt = f"""새로운 {target_zone_name} 재개발 매물이 포착되었습니다. 
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
     - 매물 상세 금융 정보 서술 및 예상 안전마진 계산 수치를 **볼드체** 표기. 주변 대장 아파트의 최근 1년 실거래 정보를 전용면적(평형), 거래 연월, 금액을 구체적으로 인용하며 비교. **이번 매물이 34평형(전용 84타입)이므로 실거래가를 인용할 때 반드시 [10. 국토교통부 실거래가 표 이미지 글자] OCR 결과를 바탕으로 주변 대장 아파트 34평형(전용 84m² 내외)의 실제 최근 실거래가(계약 연월, 거래 금액 등) 정보를 100% 팩트에 기반하여 정확하게 인용하고, 절대로 예시 수치('34.5억')나 임의의 다른 가격을 지어내지 마십시오. 바로 그 아래에 [IMAGE_11] (국토교통부 아파트 최신 실거래가 표 이미지)를 배치하여 독자가 실제 거래 내역을 표로 직접 확인할 수 있게 해주십시오.**
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

### [필수 반영] 3단계 핵심 이미지 OCR 데이터 정보
{ocr_summary_clean}
"""

        async def run_single_agent(sys_inst, pr, signal_to_emit, filename):
            # 최종 원고 작성은 항상 원격 고성능 Gemini API를 사용하도록 강제 (OCR 및 서브에이전트만 로컬 허용)
            use_local_ai = False
            local_success = False
            full_text = ""
            
            if use_local_ai:
                self.log_signal.emit("🤖 [Local AI] 1순위 로컬 LM Studio 가동 시도 중...")
                try:
                    import requests
                    import asyncio
                    loop = asyncio.get_event_loop()
                    
                    def check_model():
                        return requests.get("http://127.0.0.1:1234/v1/models", timeout=3).json()
                    model_req = await loop.run_in_executor(None, check_model)
                    active_model = model_req["data"][0]["id"]
                    
                    self.log_signal.emit(f"🤖 [Local AI] 로컬 모델 '{active_model}' 호출 중...")
                    
                    def call_local():
                        url = "http://127.0.0.1:1234/v1/chat/completions"
                        headers = {"Content-Type": "application/json"}
                        data = {
                            "model": active_model,
                            "messages": [
                                {"role": "system", "content": sys_inst},
                                {"role": "user", "content": pr}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 16000,
                            "stream": False
                        }
                        res = requests.post(url, headers=headers, json=data, timeout=180)
                        if res.status_code != 200:
                            raise RuntimeError(f"HTTP {res.status_code}: {res.text[:100]}")
                        return res.json()
                        
                    response_data = await loop.run_in_executor(None, call_local)
                    full_text = response_data["choices"][0]["message"]["content"]
                    local_success = True
                    self.log_signal.emit("✅ [Local AI 완료] 로컬 LM Studio에서 원고 작성을 완료했습니다!")
                    
                    signal_to_emit.emit("")  # Clear placeholder logs
                    cleaned_draft = filter_planning_thoughts(full_text)
                    signal_to_emit.emit(str(seo_tools.redact_secrets(cleaned_draft)))
                    
                except Exception as local_err:
                    self.log_signal.emit(f"⚠️ [Local AI 실패] 로컬 LM Studio 연결 실패 또는 오류 ({local_err}). 2순위 원격 Gemini API로 Fallback 전환합니다...")
            
            if not local_success:
                self.log_signal.emit("☁️ [원격 AI] 2순위 원격 Gemini API (Agent Config) 가동 중...")
                config = LocalAgentConfig(
                    tools=[
                        seo_tools.list_blog_posts,
                        seo_tools.read_blog_post,
                        seo_tools.get_korean_law,
                        seo_tools.get_recent_apartment_deal
                    ],
                    system_instructions=sys_inst,
                    capabilities=types.CapabilitiesConfig(
                        enable_subagents=False
                    ),
                    policies=[
                        policy.allow_all()
                    ]
                )
                
                step_texts = {}
                generation_failed = False
                error_msg = ""
                try:
                    async with Agent(config) as agent:
                        response = await agent.chat(pr)
                        signal_to_emit.emit("")  # Clear placeholder logs
                        last_logged_step = -1
                        async for chunk in response.chunks:
                            if isinstance(chunk, types.Text):
                                step_idx = chunk.step_index
                                if step_idx not in step_texts:
                                    step_texts[step_idx] = ""
                                    if last_logged_step != -1 and last_logged_step in step_texts:
                                        prev_text = step_texts[last_logged_step].strip()
                                        if prev_text:
                                            self.log_signal.emit(f"⚙️ [AI Action] {prev_text}")
                                    last_logged_step = step_idx
                                step_texts[step_idx] += chunk.text
                                
                                max_step = max(step_texts.keys())
                                cleaned_draft = filter_planning_thoughts(step_texts[max_step])
                                signal_to_emit.emit(str(seo_tools.redact_secrets(cleaned_draft)))
                            elif isinstance(chunk, types.Thought):
                                self.log_signal.emit(f"💭 [AI Thinking] {chunk.text}")
                    if step_texts:
                        max_step = max(step_texts.keys())
                        full_text = filter_planning_thoughts(step_texts[max_step])
                except Exception as e:
                    generation_failed = True
                    error_msg = str(e)
                    self.log_signal.emit(f"⚠️ [AI Generation Exception] 원고 생성 도중 오류/타임아웃 발생: {e}")
                    self.log_signal.emit("⚠️ 타임아웃/오류로 중단된 시점까지의 부분 텍스트 복구를 시도합니다.")
                    
            if step_texts and not full_text.strip():
                max_step = max(step_texts.keys())
                full_text = filter_planning_thoughts(step_texts[max_step])

            if not full_text.strip():
                if generation_failed:
                    self.log_signal.emit(f"\n❌ [AI 기획 에러] 원고 생성 전 오류 발생 ({error_msg}). 고품질 서프로 기본 백업 템플릿을 적용합니다.")
                else:
                    self.log_signal.emit(f"\n❌ [AI 기획 에러] {filename} 원고 생성 결과가 비어 있습니다. 고품질 서프로 기본 백업 템플릿을 적용합니다.")
                
                p_sale = self.atcl_info.get('p_sale', '-')
                p_premium = self.atcl_info.get('p_premium', '-')
                invest_price = self.atcl_info.get('invest_price', '-')
                p_rights = self.atcl_info.get('p_rights', '-')
                p_rent = self.atcl_info.get('p_rent', '-')
                p_total = self.atcl_info.get('p_total', '-')
                p_margin = self.atcl_info.get('p_margin', '-')
                final_tax_str = self.atcl_info.get('final_tax_str', '-')
                comp_type = self.atcl_info.get('comp_type', '-')
                status_main = self.atcl_info.get('status_main', '-')
                constructor = self.atcl_info.get('constructor', '-')
                scale = self.atcl_info.get('scale', '-')
                total_house = self.atcl_info.get('total_house', '-')
                address = self.atcl_info.get('address', '-')
                phone = self.atcl_info.get('phone', '-')

                fallback_draft = f"""| 구분 | 상세 내용 |
| --- | --- |
| 매매가격 | {p_sale}억 원 |
| 프리미엄 (P) | {p_premium}억 원 |
| 초기 실투자금 | {invest_price}억 원 |
| 감정평가액 (권리가액) | {p_rights}억 원 |
| 임대 보증금 | {p_rent}억 원 |
| 예상 총 매수가격 | {p_total}억 원 |
| 예상 안전마진 | **{p_margin}억 원** |
| 예상 취득세 | {final_tax_str} |

[IMAGE_1]

## 🔍 {target_keyword} 사업 개요 및 규제 팩트 체크
안녕하세요! 우리 프밀리님들! {target_zone_name}에 드디어 우수한 매물이 포착되어 신속하게 브리핑을 준비했습니다. {target_zone_name} 재개발 사업은 현재 {status_main} 단계로 순조롭게 진행되고 있습니다. 총 {total_house}세대 규모의 프리미엄 대단지로 시공사 {constructor}의 하이엔드 브랜드 시공을 맡아 이 지역의 새로운 랜드마크로 떠오를 예정입니다. 조합원 수는 {self.atcl_info.get('members', '-')}명 남짓으로 사업성이 우수하며, {scale} 규모로 압도적인 단지를 형성할 것입니다.

[IMAGE_2]

[IMAGE_3]

## 💰 {target_keyword} 프리미엄 및 초기투자금 상세 분석
[IMAGE_4]

본 매물의 매매가는 {p_sale}억 원이며 프리미엄은 {p_premium}억 원, 초기투자금은 {invest_price}억 원이 필요합니다. 감정평가액은 {p_rights}억 원이고 임대 보증금은 {p_rent}억 원으로 전세 안고 진입 시 실투자금 부담을 크게 낮출 수 있습니다. 이 매물의 예상 총 매수가격은 {p_total}억 원이며, 예상되는 안전마진은 무려 **{p_margin}억 원**에 달합니다. 

[IMAGE_11]

추가분담금 총액은 조합 분양 평형에 맞게 결정될 예정이며, 계약금, 중도금, 잔금 순서로 자금 일정에 따라 단계별로 납부하게 됩니다. 또한 본 구역 취득 시 무주택자는 멸실 전 일반 주택 취득세율(1.1%~3.5%)을 적용받는 것이 유리할 수 있지만, 다주택자의 경우 건물이 철거된 토지(나대지) 상태로 매매하여 4.6% 단일 토지세율을 적용받는 것이 세금 중과 회복 면에서 훨씬 유리합니다.

[IMAGE_5]

[IMAGE_6]

[IMAGE_7]

## 📍 {target_keyword} 핵심 교통망 및 미래 가치 입지 분석
{target_zone_name}은 여의도와 강남을 연결하는 최고의 입지적 메리트를 제공합니다.

다만, {regulation_status_text}
`도시 및 주거환경정비법 제39조`에 따르면 조합 설립 인가 후 정비사업의 건축물 또는 토지를 양수한 자는 조합원이 될 수 없으나, 세대원의 근무상 형편 등 부득이한 사유로 양도하는 경우 등 대통령령으로 정하는 특별한 사유가 있는 경우에는 조합원이 될 수 있도록 규정하고 있으므로 조합사무실(전화번호: {phone})에서 상세 내용을 크로스체크 하시기 바랍니다.

[IMAGE_8]

[IMAGE_9]

#{target_keyword} #{area_name}재개발 #{area_redev_tag} #재개발 #부동산
"""
                full_text = fallback_draft
            
            full_text = enforce_rules_in_draft(full_text, self.atcl_info)
            signal_to_emit.emit(str(seo_tools.redact_secrets(full_text)))
            
            title = f"{target_zone_name} 재개발 매물 분석 브리핑"
            title_match = re.search(r'^#\s+(.+)$', full_text, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
            elif "title:" in full_text:
                t_match = re.search(r'title:\s*"(.*?)"', full_text)
                if t_match:
                    title = t_match.group(1)
                    
            tags = [f"{area_name}{zone_num}구역" if zone_num else area_name, target_keyword, area_redev, area_redev_tag]
            
            # 파일 강제 쓰기 예외 처리 보강
            try:
                try:
                    seo_tools.save_blog_post(filename, title, full_text, tags)
                    self.log_signal.emit(f"💾 [파일 저장 완료] {filename} (길이: {len(full_text)}자)")
                except Exception as file_err:
                    self.log_signal.emit(f"❌ [파일 저장 에러] {filename} 쓰기 실패: {file_err}. 직접 쓰기 시도...")
                    save_dir = "/Users/seopro/Desktop/완전자동화/blog_posts"
                    os.makedirs(save_dir, exist_ok=True)
                    filepath = os.path.join(save_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(full_text)
                    self.log_signal.emit(f"💾 [파일 강제 저장 완료 (직접 쓰기)] {filepath}")
            except Exception as force_err:
                self.log_signal.emit(f"❌ [파일 강제 저장 최종 실패] {force_err}")
                    
            return full_text

        if self.feedback_report and self.previous_draft:
            self.log_signal.emit("\n🔄 [Feedback Grader] 이전 원고와 SEO 피드백 보고서를 바탕으로 정밀 자동 재교정을 가동합니다...")
            clean_tips = []
            for tip in self.feedback_report.get('improvement_tips', []):
                if "⚠️" in tip or "💡" in tip or "🚨" in tip:
                    clean_tips.append(tip)
            tips_text = "\n".join(clean_tips) if clean_tips else "원고에 전반적인 완성도 보완이 필요합니다."
            
            rewrite_prompt = f"""당신이 작성한 이전 블로그 원고에서 일부 SEO 미달 사항(피드백)이 감지되었습니다.
기존 원고를 바탕으로 아래의 [매물 팩트 데이터] 및 [SEO 개선 요구사항]들을 **100% 한 번에 완벽히 교정 및 반영**하여 수정된 최종 원고를 작성해 주십시오.

### [매물 팩트 데이터]
- 구역: {target_zone_name}
- 위치: {self.atcl_info.get('address', '')}
- 진행현황: {self.atcl_info.get('status_main', '')} / {self.atcl_info.get('status_sub', '')}
- 총 세대수: {self.atcl_info.get('total_house', '')}
- 조합원 수: {self.atcl_info.get('members', '')}
- 시공사: {self.atcl_info.get('constructor', '')}
- 사업규모: {self.atcl_info.get('scale', '')}
- 준공예상: {self.atcl_info.get('completion', '')}
- 이주비조건: {self.atcl_info.get('move_cost', '')}
- 조합원 비례율: {self.atcl_info.get('rate', '')}
- 조합원분양가: {self.atcl_info.get('member_price', '')}
- 추가분담금: {self.atcl_info.get('contribution', '')}
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

### [이전 원고]
{self.previous_draft}

### [SEO 개선 요구사항 (반드시 모두 해결할 것)]
{tips_text}

### 수정 시 필수 준수 사항:
1. 기존 원고의 전체적인 전문가 스타일(서프로 페르소나), 매끄러운 흐름, 그리고 이미지 위치 마커(`[IMAGE_1]` ~ `[IMAGE_9]`)의 배치 구조는 훼손하지 말고 그대로 유지하십시오.
2. 피드백 요구사항에 기재된 내용들을 정확하게 파악하여 단 하나의 누락도 없이 전부 처리하십시오. 특히 **"매물 가격 정보를 요약하는 표(Table)가 발견되지 않았습니다" 라는 피드백이 있을 경우, 본문 내 적절한 위치(예: 매물 가격을 설명하는 IMAGE_4 근처)에 매매가, 프리미엄, 초기투자금, 권리가 등의 가격 요약 마크다운 표(Table)를 무조건 포함**하십시오.
3. 원고의 풍부한 깊이와 상세 분석 분량(1,500자 ~ 2,000자 내외)이 축소되거나 요약되지 않도록 본문의 길이와 디테일을 유지 또는 확장하여 작성해 주십시오. (절대 기존 원고를 임의로 크게 줄여 요약하지 마십시오.)
4. 네이버 검색에 최적화될 수 있도록 핵심 키워드 '{target_keyword}'이 자연스럽게 들어가도록 신중을 기해 주십시오.
5. 어떠한 본문 외의 설명이나 메타멘트도 절대 넣지 말고, 오직 즉시 복사하여 업로드할 수 있는 완성된 마크다운 본문만을 처음부터 끝까지 깔끔하게 출력하십시오.
"""
            if self.active_tab_idx == 1:
                self.log_signal.emit("🤖 [Main Agent] 탭 2: SEO 최적화 버전 재교정을 가동합니다...")
                prompt_seo = rewrite_prompt + f"""
                
### [SEO 최적화 버전용 특수 주의사항]
- 스마트폰 가독성을 위해 문단을 극도로 짧게 끊으십시오. 모든 문단은 **2~3줄 이내**여야 합니다.
- 타겟 키워드 '{target_keyword}'이 띄어쓰기 없이 정확히 **5~7회**만 삽입되도록 횟수를 엄밀히 맞추십시오.
- 모든 금액 및 안전마진 수치는 마크다운 볼드체(예: **5.6억**)를 적용하십시오.
"""
                await run_single_agent(
                    dynamic_instructions_seo, 
                    prompt_seo, 
                    self.draft_seo_ready_signal, 
                    filename_seo
                )
            else:
                self.log_signal.emit("🤖 [Main Agent] 탭 1: 일반 버전 재교정을 가동합니다...")
                await run_single_agent(
                    dynamic_instructions, 
                    rewrite_prompt, 
                    self.draft_ready_signal, 
                    filename_normal
                )
                
            self.log_signal.emit("\n✅ [재교정 완료] 피드백 반영 재교정 원고 작성이 완성되었습니다!")
            self.finished_signal.emit()

        else:
            if self.draft_type in ["normal", "both"]:
                self.log_signal.emit("\n🤖 [Main Agent] 1단계: 일반 버전 서프로 카피라이터 집필을 가동합니다...")
                await run_single_agent(
                    dynamic_instructions, 
                    base_prompt, 
                    self.draft_ready_signal, 
                    filename_normal
                )
            
            if self.draft_type in ["seo", "both"]:
                self.log_signal.emit("\n🤖 [Main Agent] 2단계: SEO 최적화 버전 서프로 카피라이터 집필을 가동합니다...")
                prompt_seo = base_prompt + f"""

### [중요] 버전 2 전용 SEO 최적화 특수 집필 지침:
1. 스마트폰 가독성을 위해 문단을 매우 짧게 끊어 써 주십시오. 각 문단은 줄바꿈 기준으로 **2~3줄 이내**로 작성되어야 합니다.
2. 타겟 키워드 '{target_keyword}'이 본문 전체에서 띄어쓰기 없이 정확히 **5~7회** 삽입되도록 개수를 맞추어 주십시오.
3. 예상 안전마진 등의 수치는 반드시 마크다운 볼드체(예: **5.6억**)를 적용하여 표기해 주십시오.
4. 불필요한 수식어와 뇌피셜(환각)을 일절 생략하고 극도의 정밀함과 사실만을 정갈하고 명확하게 서술해 주십시오.
"""
                await run_single_agent(
                    dynamic_instructions_seo, 
                    prompt_seo, 
                    self.draft_seo_ready_signal, 
                    filename_seo
                )
            
            if self.draft_type == "normal":
                self.log_signal.emit("\n✅ [AI 기획 완료] 일반 초안 작성이 정상적으로 완료되었습니다!")
            elif self.draft_type == "seo":
                self.log_signal.emit("\n✅ [AI 기획 완료] SEO 최적화 초안 작성이 정상적으로 완료되었습니다!")
            else:
                self.log_signal.emit("\n✅ [AI 기획 완료] 일반 및 SEO 최적화 초안 2가지가 모두 정상적으로 작성되었습니다!")
            self.finished_signal.emit()
