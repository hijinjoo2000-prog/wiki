# P-Reinforce 분류 정책 (Policy)

이 파일은 지식 구조화 에이전트 `P-Reinforce`가 지식을 분류하고 최적화할 때 따르는 규칙 및 보상 정책 설정 파일입니다. 사용자의 피드백에 의해 동적으로 업데이트될 수 있습니다.

## ⚙️ 보상 함수 가중치 (Reward Weights)
현재 보상 함수 $R$의 가중치 설정 값입니다.
- **$w_1$ (Categorization Accuracy)**: `0.5`
- **$w_2$ (Graph Density)**: `0.3`
- **$w_3$ (Redundancy Penalty)**: `0.2`

$$\text{Total Reward } R = 0.5 \times \text{Accuracy} + 0.3 \times \text{Density} - 0.2 \times \text{Redundancy}$$

---

## 📂 카테고리 정의 및 분류 기준
1. **Projects (`🛠️ Projects/`)**
   - 목표 중심의 실시간 진행 상황 및 프로젝트 관리
   - 예시: `AI_City_Project` 등과 같이 구체적인 결과물을 목표로 진행되는 프로젝트 지식
2. **Topics (`💡 Topics/`)**
   - 개념 중심의 도메인 지식
   - 예시: 부동산, 코딩 언어, 프레임워크 명세, 철학, 경제 등
3. **Decisions (`⚖️ Decisions/`)**
   - 의사결정 기록 및 논리적 판단 근거
   - 예시: 특정 기술 스택을 선택한 이유, 아키텍처 의사결정 레코드(ADR)
4. **Skills (`🚀 Skills/`)**
   - 실행 중심의 유용한 프롬프트, 팁, 스크립트 템플릿 코드
   - 예시: 자동화 스크립트 코드, 시스템 지침서, 개발 환경 셋팅 가이드

---

## 📈 임계치 규칙 (Threshold Rules)
- **분류 유사도**: LLM 기준 유사도가 `85%` 이상인 기존 카테고리/폴더가 있을 경우 해당 폴더로 자동 배치. 미달 시 신규 카테고리 폴더 생성.
- **폴더 한계선**: 특정 폴더의 파일 개수가 `12개`를 초과하면, 에이전트는 해당 폴더 내 문서들의 연관성을 다시 분석하여 하위 카테고리(Sub-folders)로 분리하고 `Graph.json` 및 문서 메타데이터를 재구조화함.
