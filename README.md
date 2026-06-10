# 🌐 P-Reinforce LLM-Wiki Knowledge Engine

> **"지식의 중력을 거스르는 자율 분류 지식 정원사"**
> Andre Karpathy의 LLM-Wiki 아키텍처와 강화학습(RL)의 가치 극대화 원리를 결합하여, 산재된 지식의 파편을 실시간으로 감지하고 완벽한 쌍방향 지식 그래프 구조로 빌드하는 에이전트 시스템입니다.

---

## 🚀 핵심 미션 (Core Mission)
1. **Raw 데이터 실시간 모니터링**: `00_Raw/` 폴더에 날짜별로 유입되는 가공되지 않은 데이터(텍스트, 마크다운 등)를 지능적으로 감지합니다.
2. **동적 폴더 구조화**: 고정된 분류 트리를 사용하지 않고, 지식의 맥락에 따라 최적의 폴더 위계를 동적으로 생성하고 배치합니다.
3. **쌍방향 지식 링크망 구축**: 개별 문서 간의 연관 관계를 분석해 `[[쌍방향 링크]]`로 연결하며 거대한 지식망(External Brain)을 형성합니다.
4. **Git Sync를 통한 타임라인 보존**: 모든 문서 생성, 업데이트 및 분류 변경 이력을 GitHub 커밋으로 관리하여 타임라인을 투명하게 영속화합니다.

---

## 📂 표준 폴더 구조 (Directory Structure)

```plaintext
root/
├── 00_Raw/                 # [불변] 사용자로부터 입력된 가공되지 않은 날것의 데이터
│   └── YYYY-MM-DD/         # 날짜별 원본 데이터 보관 (Source of Truth)
│
├── 10_Wiki/                # [자동 구조화] 에이전트가 RL 정책에 따라 빌드하는 지식 베이스
│   ├── 🛠️ Projects/        # 목표 중심 (현재 진행 중인 프로젝트, 시스템 설계도 등)
│   ├── 💡 Topics/          # 개념 중심 (부동산, 코딩, 철학 등 도메인 지식)
│   ├── ⚖️ Decisions/       # 의사결정 중심 (왜 이렇게 판단했는지 논리적 근거 기록)
│   └── 🚀 Skills/          # 실행 중심 (사용자만의 프롬프트, 팁, 템플릿 코드)
│
├── 20_Meta/                # [시스템] 지식 엔진의 두뇌 데이터 및 인덱스
│   ├── Graph.json          # 지식 간의 관계 및 노드 데이터 (시각화/그래프용)
│   ├── Policy.md           # 사용자 피드백이 반영된 분류 정책 설정 파일
│   └── Index.md            # 위키 전체의 입구 (Table of Contents)
│
└── dashboard/              # 지식 시각화 및 에이전트 관리를 위한 웹 대시보드
```

---

## 📝 지식 문서 변환 규격 (The Wiki Template)

에이전트가 최종적으로 생성/업데이트해야 하는 마크다운 형식입니다.

```markdown
---
id: {{UUID}}
category: "[[10_Wiki/Path/To/Folder]]"
confidence_score: 0.0 ~ 1.0
tags: [태그1, 태그2]
last_reinforced: YYYY-MM-DD
github_commit: "{{commit_hash}}"
---

# [[개념/엔티티 이름]]

## 📌 한 줄 포착 (The Karpathy Summary)
> (이 지식 베이스를 관통하는 핵심 요약을 1~2문장으로 직관적으로 기술)

## 📊 구조화된 지식 (Synthesized Content)
- (원본 소스로부터 종합 및 정제된 핵심 내용 상세 기술)
- (수치적 데이터, 투자 정보, 혹은 기술적 뼈대를 유실 없이 Bullet 형식으로 정렬)

## 🔗 지식 연결망 (Knowledge Connections)
- **Related Topics:** [[연관 개념 A]], [[연관 개념 B]]
- **Projects/Contexts:** [[관련 프로젝트명]]
- **Contradictions/Notes:** (출처 간의 모순점이나 리스크, 사용 시 주의사항을 날카롭게 추적 분석)

updated: YYYY-MM-DD
```

---

## ⚙️ 엔진 작동법 (How It Works)

### 1. 지식 강화 엔진 실행
- `00_Raw/` 에 신규 데이터가 유입되면 엔진을 트리거하여 자동으로 문서를 파싱하고, 카테고리를 분류하며, 인덱스를 업데이트하고 깃으로 동기화합니다.
```bash
python3 reinforce.py
```
*(실행 전 `.env` 파일에 `GEMINI_API_KEY` 환경 변수가 필요합니다.)*

### 2. 시각화 대시보드 실행
- 지식의 전체 연결망을 한눈에 볼 수 있는 인터랙티브 웹 대시보드를 제공합니다.
```bash
# 대시보드 백엔드 API 서버 실행 (포트 5001)
node dashboard/server.js

# 대시보드 프론트엔드 (Vite React) 실행 (포트 5173)
cd dashboard
npm install
npm run dev
```

---

## 🧠 강화학습 분류 규칙 (RL Logic)
지식 배치 시 아래 보상 함수 $R$을 극대화하도록 구성되어 있습니다.
$$R = w_1(\text{Categorization Accuracy}) + w_2(\text{Graph Density}) - w_3(\text{Redundancy Penalty})$$

- **상태(State) 분석**:
  - 현재 `10_Wiki/` 하위의 모든 폴더 트리와 `20_Meta/Graph.json`의 지식 연결망 상태를 실시간으로 파악합니다.
- **분류 및 폴더링 (Action)**:
  - **기존 분류**: 기존 분류군과 유사도가 85% 이상일 시 기존 폴더로 스마트 배치됩니다.
  - **신규 생성**: 기존 카테고리에 맞지 않는 새로운 개념 등장 시 즉시 새로운 폴더 노드를 구성합니다.
  - **구조 재설계**: 특정 폴더의 파일 개수가 12개를 초과하면 하위 카테고리들로 자동 재분할하여 폴더 구조를 Refactoring합니다.
