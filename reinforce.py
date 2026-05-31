import os
import sys
import json
import uuid
import datetime
import subprocess
from pathlib import Path

# 1. 자동 패키지 설치 기능
REQUIRED_PACKAGES = ["google-generativeai", "python-dotenv"]

def install_dependencies():
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"📦 패키지 설치 중: {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

import google.generativeai as genai
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# Gemini API 초기화
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # 혹시 .env 파일이 없고 active workspace 외부나 환경 변수에 있을 경우를 대비
    # 없으면 사용자에게 경고를 하지만, 백그라운드 구동을 위해 기본값/빈값 에러 방지
    print("⚠️ 경고: GEMINI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 만들거나 환경변수를 설정해주세요.")

genai.configure(api_key=GEMINI_API_KEY)

# 2. 경로 설정
BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = BASE_DIR / "00_Raw"
WIKI_DIR = BASE_DIR / "10_Wiki"
META_DIR = BASE_DIR / "20_Meta"
GRAPH_FILE = META_DIR / "Graph.json"
POLICY_FILE = META_DIR / "Policy.md"
INDEX_FILE = META_DIR / "Index.md"
PROCESSED_LOG_FILE = META_DIR / "processed_files.json"

# 3. 로깅 도우미
def log(message):
    print(f"🤖 [P-Reinforce]: {message}")

# 4. 초기 메타데이터 파일 확인 및 적재
def load_json_file(path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"JSON 로드 오류 ({path.name}): {e}")
        return default

def save_json_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_file(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# 5. Git 커밋 유틸리티
def run_git_command(args):
    try:
        result = subprocess.run(["git"] + args, cwd=BASE_DIR, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log(f"Git 명령 오류 (git {' '.join(args)}): {e.stderr}")
        return None

# 6. LLM 도우미 함수
def call_gemini(prompt, system_instruction=None):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 없습니다. API 키를 설정해주세요.")
    
    # 2.5 Flash 모델 사용 (빠르고 저렴하며 텍스트 처리에 적합)
    model_name = "gemini-2.5-flash"
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        log(f"Gemini API 호출 중 에러 발생 (모델 {model_name}): {e}")
        # fallback to 1.5-flash if 2.5-flash is not available
        try:
            log("Gemini 1.5 Flash 모델로 재시도합니다...")
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
            response = model.generate_content(prompt)
            return response.text
        except Exception as ex:
            log(f"Gemini 1.5 Flash 재시도 실패: {ex}")
            raise ex

# 7. 카테고리 유사도 분석 및 재구조화 로직
def get_existing_wiki_paths():
    """10_Wiki 하위의 실제 폴더 경로(카테고리 목록)를 가져옵니다."""
    paths = []
    # 4가지 표준 대분류
    categories = ["Projects", "Topics", "Decisions", "Skills"]
    for cat in categories:
        cat_dir = WIKI_DIR / cat
        if cat_dir.exists():
            paths.append(f"10_Wiki/{cat}")
            for root, dirs, files in os.walk(cat_dir):
                for d in dirs:
                    rel_path = Path(root) / d
                    paths.append(rel_path.relative_to(BASE_DIR).as_pos_path())
    # Unix-style path로 치환
    return [p.replace("\\", "/") for p in paths]

Path.as_pos_path = lambda self: self.as_posix() if hasattr(self, 'as_posix') else str(self).replace('\\', '/')

def determine_category_and_metadata(file_name, file_content):
    """문서의 내용을 분석하여 적절한 폴더 경로와 카테고리를 LLM을 통해 결정합니다."""
    existing_paths = get_existing_wiki_paths()
    policy_content = read_file(POLICY_FILE)
    
    system_instruction = (
        "너는 P-Reinforce 지식 엔진의 분류 및 구조화 아키텍트다.\n"
        "제공된 문서를 분석하여 가장 적합한 위키 분류 폴더 경로를 지정하고 지식을 요약 및 연결하라.\n"
        "반드시 아래 JSON 형식으로만 응답하라. 다른 설명이나 텍스트를 절대 추가하지 마라.\n\n"
        "JSON 응답 규격:\n"
        "{\n"
        "  \"suggested_category_path\": \"10_Wiki/Topics/SubFolder 또는 10_Wiki/Projects 등\",\n"
        "  \"confidence_score\": 0.95,\n"
        "  \"tags\": [\"태그1\", \"태그2\"],\n"
        "  \"concept_name\": \"문서의 핵심 개념/엔티티 명칭 (예: AI_City_Master_Plan)\",\n"
        "  \"summary\": \"핵심 요약 1~2문장\",\n"
        "  \"structured_bullets\": [\"- 핵심 내용 1\", \"- 핵심 내용 2\"],\n"
        "  \"related_topics\": [\"연관_개념_A\", \"연관_개념_B\"],\n"
        "  \"related_projects\": [\"관련_프로젝트_명\"],\n"
        "  \"contradictions_notes\": \"출처 간 모순점, 리스크 또는 주의사항\"\n"
        "}"
    )
    
    prompt = f"""
---
기존 위키 폴더 목록:
{json.dumps(existing_paths, ensure_ascii=False, indent=2)}

강화학습 분류 정책(Policy.md):
{policy_content}

처리할 파일명: {file_name}
파일 본문:
{file_content}
---

위 내용을 바탕으로 JSON 응답 규격에 맞게 데이터를 추출해줘. 
특히 `suggested_category_path`는 기존 폴더 중 가장 유사한 것(유사도 85% 이상)을 선택하거나, 
마땅한 폴더가 없다면 정책 가이드라인에 맞추어 `10_Wiki/Topics/새폴더명` 등과 같이 동적으로 새 경로를 제시해라.
"""
    
    response_text = call_gemini(prompt, system_instruction)
    # JSON 파싱
    try:
        # LLM 응답에서 markdown block ```json ... ``` 제거
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        return json.loads(clean_text)
    except Exception as e:
        log(f"LLM 응답 JSON 파싱 실패. 응답 텍스트:\n{response_text}\n에러: {e}")
        # Fallback 임시 데이터
        return {
            "suggested_category_path": "10_Wiki/Topics",
            "confidence_score": 0.5,
            "tags": ["General"],
            "concept_name": Path(file_name).stem,
            "summary": "자동 분류 및 요약 실패로 생성된 임시 문서입니다.",
            "structured_bullets": ["- 원본 문서를 참고하십시오."],
            "related_topics": [],
            "related_projects": [],
            "contradictions_notes": "없음"
        }

# 8. 지식 그래프 Graph.json 업데이트
def update_knowledge_graph(doc_id, concept_name, category_path, tags, related_topics, related_projects, file_path_rel):
    graph = load_json_file(GRAPH_FILE, {"nodes": [], "links": []})
    
    # 노드 갱신 또는 추가
    node_id = doc_id
    # 기존 노드 중 이름이 같거나 ID가 같은 것 확인
    existing_node = None
    for node in graph["nodes"]:
        if node["id"] == node_id or node["label"] == concept_name:
            existing_node = node
            break
            
    node_data = {
        "id": node_id,
        "label": concept_name,
        "category": category_path,
        "path": file_path_rel,
        "tags": tags,
        "updated": datetime.date.today().isoformat()
    }
    
    if existing_node:
        existing_node.update(node_data)
    else:
        graph["nodes"].append(node_data)
        
    # 링크(엣지) 갱신
    # 1단계: 이 노드와 관련된 기존 링크 삭제
    graph["links"] = [link for link in graph["links"] if link["source"] != node_id and link["target"] != node_id]
    
    # 2단계: 신규 링크 추가 (쌍방향 링크 구조이므로, Graph.json에서는 단방향 혹은 양방향으로 기록 가능)
    all_connections = related_topics + related_projects
    for target_label in all_connections:
        # 대상 노드가 그래프에 존재하는지 확인
        target_id = None
        for n in graph["nodes"]:
            if n["label"] == target_label:
                target_id = n["id"]
                break
        
        # 대상 노드가 아직 그래프에 없다면, 미분류 가상 노드를 추가해 둠
        if not target_id:
            target_id = str(uuid.uuid4())
            graph["nodes"].append({
                "id": target_id,
                "label": target_label,
                "category": "10_Wiki/Topics/Uncategorized",
                "path": "",
                "tags": [],
                "updated": datetime.date.today().isoformat()
            })
            
        graph["links"].append({
            "source": node_id,
            "target": target_id,
            "type": "related"
        })
        # 쌍방향 링크 기록
        graph["links"].append({
            "source": target_id,
            "target": node_id,
            "type": "related"
        })
        
    save_json_file(GRAPH_FILE, graph)
    log("Graph.json 업데이트 완료.")

# 9. Index.md 테이블 오브 콘텐츠 갱신
def update_index_md():
    graph = load_json_file(GRAPH_FILE, {"nodes": [], "links": []})
    
    # 카테고리별 분류
    categories = {
        "Projects": [],
        "Topics": [],
        "Decisions": [],
        "Skills": []
    }
    
    for node in graph["nodes"]:
        if not node["path"]: # 실존하지 않는 가상 연결 노드는 제외
            continue
            
        path_str = node["category"]
        matched = False
        for cat in categories.keys():
            if f"10_Wiki/{cat}" in path_str:
                categories[cat].append(node)
                matched = True
                break
        if not matched:
            # 매칭 안 되면 기본 Topics로 분류
            categories["Topics"].append(node)
            
    # Index.md 텍스트 생성
    content = []
    content.append("# 🌐 P-Reinforce Wiki Index\n")
    content.append("P-Reinforce 자동 지식 구조화 엔진이 빌드하는 지식 베이스의 입구입니다. 아래 카테고리별로 실시간 분류된 지식 문서들이 연결됩니다.\n")
    content.append("---\n")
    
    emoji_map = {
        "Projects": "🛠️ Projects",
        "Topics": "💡 Topics",
        "Decisions": "⚖️ Decisions",
        "Skills": "🚀 Skills"
    }
    
    for cat, nodes in categories.items():
        content.append(f"## {emoji_map[cat]}")
        content.append("*현재 분류된 목록*")
        if not nodes:
            content.append("- (아직 등록된 문서가 없습니다.)\n")
        else:
            for node in nodes:
                # Relative link
                link_path = node["path"]
                content.append(f"- [{node['label']}]({link_path})")
            content.append("") # 줄바꿈
            
    write_file(INDEX_FILE, "\n".join(content))
    log("Index.md 업데이트 완료.")

# 10. 폴더 내 파일 12개 초과 시 재구조화 로직
def check_and_refactor_folders():
    """10_Wiki 하위 폴더 중 파일이 12개를 초과하는 폴더가 있는지 체크하고,
       있을 경우 LLM을 통해 하위 카테고리로 재구조화합니다.
    """
    log("폴더 트리 재구조화(12개 초과 여부) 점검 중...")
    wiki_root = WIKI_DIR
    
    for root, dirs, files in os.walk(wiki_root):
        md_files = [f for f in files if f.endswith(".md") and f != ".gitkeep"]
        if len(md_files) > 12:
            folder_path = Path(root)
            rel_folder_path = folder_path.relative_to(BASE_DIR).as_pos_path()
            log(f"⚠️ 폴더 '{rel_folder_path}'의 파일 개수가 {len(md_files)}개로 한계치(12개)를 초과했습니다. 재구조화를 실행합니다.")
            
            # 파일 정보 수집
            file_summaries = []
            for file_name in md_files:
                file_path = folder_path / file_name
                content = read_file(file_path)
                # Front matter 아래 📌 한 줄 포착(요약)을 찾거나, 파일명 활용
                summary = ""
                for line in content.split("\n"):
                    if line.strip().startswith(">"):
                        summary = line.strip()[1:].strip()
                        break
                file_summaries.append({
                    "name": file_name,
                    "summary": summary
                })
                
            # LLM에게 하위 카테고리 기획 요청
            system_instruction = (
                "너는 지식 저장소 폴더 재구조화 전문가다.\n"
                "파일 목록과 요약을 보고, 이를 2~4개의 논리적인 하위 폴더(Sub-folders)로 그룹화하라.\n"
                "반드시 아래 JSON 포맷으로만 응답하라. 다른 설명이나 텍스트를 절대 추가하지 마라.\n\n"
                "JSON 응답 규격:\n"
                "{\n"
                "  \"subfolders\": {\n"
                "    \"하위폴더명1\": [\"파일명1.md\", \"파일명2.md\"],\n"
                "    \"하위폴더명2\": [\"파일명3.md\", \"파일명4.md\"]\n"
                "  }\n"
                "}"
            )
            
            prompt = f"""
현재 초과 상태인 폴더: {rel_folder_path}
폴더 내 파일 목록 및 요약:
{json.dumps(file_summaries, ensure_ascii=False, indent=2)}

위 파일들을 어떤 논리적 하위 카테고리로 나누면 좋을지 결정해줘.
하위 폴더 이름은 직관적이고 한글/영문 모두 가능해 (예: "Backend", "Frontend", "개발_가이드" 등).
반드시 제공된 모든 마크다운 파일(.md)을 분류에 포함시켜야 해.
"""
            try:
                response_text = call_gemini(prompt, system_instruction)
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                refactor_plan = json.loads(clean_text)
                subfolders = refactor_plan.get("subfolders", {})
                
                # 파일 이동 및 메타데이터 업데이트
                for subfolder_name, file_names in subfolders.items():
                    subfolder_dir = folder_path / subfolder_name
                    subfolder_dir.mkdir(parents=True, exist_ok=True)
                    
                    for f_name in file_names:
                        src_path = folder_path / f_name
                        dest_path = subfolder_dir / f_name
                        
                        if src_path.exists() and src_path != dest_path:
                            # 1. 파일 이동
                            src_path.rename(dest_path)
                            log(f"🚚 이동: {src_path.name} -> {subfolder_name}/{f_name}")
                            
                            # 2. 파일 내부 메타데이터(category) 업데이트
                            file_content = read_file(dest_path)
                            new_category_path = f"10_Wiki/{subfolder_dir.relative_to(WIKI_DIR).as_pos_path()}"
                            # category: "[[...]]" 형태 교체
                            # 단순 문자열 치환
                            lines = file_content.split("\n")
                            for idx, line in enumerate(lines):
                                if line.strip().startswith("category:"):
                                    lines[idx] = f'category: "[[{new_category_path}]]"'
                                    break
                            write_file(dest_path, "\n".join(lines))
                            
                            # 3. Graph.json 업데이트
                            # ID를 찾기 위해 파일 파싱 또는 Graph.json에서 경로 매칭
                            graph = load_json_file(GRAPH_FILE, {"nodes": [], "links": []})
                            old_rel_path = src_path.relative_to(BASE_DIR).as_pos_path()
                            new_rel_path = dest_path.relative_to(BASE_DIR).as_pos_path()
                            
                            for node in graph["nodes"]:
                                if node["path"] == old_rel_path:
                                    node["path"] = new_rel_path
                                    node["category"] = new_category_path
                                    break
                            save_json_file(GRAPH_FILE, graph)
                            
                # Index.md 및 Graph.json 최종 재정렬
                update_index_md()
                log(f"🎉 폴더 '{rel_folder_path}' 재구조화 완료!")
                
            except Exception as e:
                log(f"재구조화 수행 중 에러 발생: {e}")

# 11. 메인 강화(Reinforce) 처리 루프
def reinforce_main():
    log("지식 강화 프로세스를 시작합니다...")
    
    # 처리 완료 로그 파일 로드
    processed_files = load_json_file(PROCESSED_LOG_FILE, [])
    
    # 00_Raw 내의 처리 대상 파일 수집
    raw_files = []
    for root, dirs, files in os.walk(RAW_DIR):
        for f in files:
            if f.endswith(".txt") or f.endswith(".md"):
                if f == ".gitkeep":
                    continue
                full_path = Path(root) / f
                rel_path = full_path.relative_to(BASE_DIR).as_pos_path()
                if rel_path not in processed_files:
                    raw_files.append((full_path, rel_path))
                    
    if not raw_files:
        log("💡 처리할 새로운 raw 데이터 파일이 없습니다.")
        return
        
    log(f"발견된 새 파일 개수: {len(raw_files)}개")
    
    for full_path, rel_raw_path in raw_files:
        log(f"📄 처리 중: {full_path.name}")
        content = read_file(full_path)
        
        # LLM을 통한 분석 및 구조화 데이터 획득
        meta = determine_category_and_metadata(full_path.name, content)
        
        # UUID 및 시간 생성
        doc_id = str(uuid.uuid4())
        today_str = datetime.date.today().isoformat()
        
        # 저장 경로 생성
        target_dir = BASE_DIR / meta["suggested_category_path"]
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 템플릿 마크다운 문서 생성
        concept_name = meta["concept_name"]
        # 파일명을 개념명에 맞추어 생성 (공백 제거 등 안전한 파일명화)
        safe_file_name = "".join([c for c in concept_name if c.isalpha() or c.isdigit() or c in (" ", "_", "-")]).strip().replace(" ", "_")
        if not safe_file_name:
            safe_file_name = f"doc_{doc_id[:8]}"
        target_file_path = target_dir / f"{safe_file_name}.md"
        
        # 이미 동일 이름의 마크다운 파일이 존재할 경우 ammend/overwrite 정책
        # 여기서는 overwrite로 처리하되 로그를 남김
        if target_file_path.exists():
            log(f"⚠️ 경고: {target_file_path.name} 파일이 이미 존재합니다. 덮어씁니다.")
            
        # Front Matter 및 템플릿 구조화
        structured_bullets_str = "\n".join(meta["structured_bullets"])
        related_topics_links = ", ".join([f"[[{t}]]" for t in meta["related_topics"]]) or "없음"
        related_projects_links = ", ".join([f"[[{p}]]" for p in meta["related_projects"]]) or "없음"
        
        wiki_template = f"""---
id: {doc_id}
category: "[[{meta['suggested_category_path']}]]"
confidence_score: {meta['confidence_score']}
tags: {json.dumps(meta['tags'], ensure_ascii=False)}
last_reinforced: {today_str}
github_commit: "pending"
---

# [[{concept_name}]]

## 📌 한 줄 포착 (The Karpathy Summary)
> {meta['summary']}

## 📊 구조화된 지식 (Synthesized Content)
{structured_bullets_str}

## 🔗 지식 연결망 (Knowledge Connections)
- **Related Topics:** {related_topics_links}
- **Projects/Contexts:** {related_projects_links}
- **Contradictions/Notes:** {meta['contradictions_notes']}

updated: {today_str}
"""
        # 임시로 파일 쓰기
        write_file(target_file_path, wiki_template)
        target_rel_path = target_file_path.relative_to(BASE_DIR).as_pos_path()
        
        # Graph.json 업데이트
        update_knowledge_graph(
            doc_id=doc_id,
            concept_name=concept_name,
            category_path=meta["suggested_category_path"],
            tags=meta["tags"],
            related_topics=meta["related_topics"],
            related_projects=meta["related_projects"],
            file_path_rel=target_rel_path
        )
        
        # Index.md 갱신
        update_index_md()
        
        # Git Commit & 해시 피드백 루프
        # 1. 파일 추가 및 최초 임시 커밋
        run_git_command(["add", "."])
        commit_msg = f"Reinforce: Add {concept_name} (UUID: {doc_id[:8]})"
        run_git_command(["commit", "-m", commit_msg])
        
        # 2. 방금 만들어진 커밋 해시 취득
        commit_hash = run_git_command(["rev-parse", "HEAD"])
        if commit_hash:
            # 3. 파일 내 "pending" 해시를 실제 해시로 갱신
            updated_content = read_file(target_file_path).replace('github_commit: "pending"', f'github_commit: "{commit_hash}"')
            write_file(target_file_path, updated_content)
            # 4. 커밋 어멘드(amend) 수행하여 변경사항 반영
            run_git_command(["commit", "--amend", "--no-edit", "-a"])
            log(f"💾 Git Commit 완료. 해시: {commit_hash}")
        
        # 처리 완료 기록
        processed_files.append(rel_raw_path)
        save_json_file(PROCESSED_LOG_FILE, processed_files)
        log(f"✅ 완료: {concept_name} -> {target_rel_path}")
        
    # 폴더 구조 한계치(12개) 초과 시 재구조화 트리거
    check_and_refactor_folders()

if __name__ == "__main__":
    reinforce_main()
