---
id: 6f36d579-1f3e-4dd1-ab4d-63dc31eba0e6
category: "[[10_Wiki/Topics/AI_Applications/Automated_Video_Production]]"
confidence_score: 0.95
tags: ["Automated Video Production", "Generative AI", "Gemini", "Veo", "FastAPI", "React", "System Design", "Master Plan"]
last_reinforced: 2026-05-31
github_commit: "b95c9abdd1872f0e07442ddeae38be745e0e35f9"
---

# [[AI_City_Master_Plan]]

## 📌 한 줄 포착 (The Karpathy Summary)
> 본 문서는 '초자동화 영상 생산 도시(AI City Master Plan)'의 초기 마스터 플랜으로, React+FastAPI 스택과 Gemini 3 및 Veo 3.1 모델을 통합하여 자동화된 영상 생성을 목표로 합니다. 도시 구조에 비유한 운영 철학을 바탕으로, 영상 생성 게이트웨이의 백엔드 아키텍처 및 4단계 AI 서비스 파이프라인 설계를 상세히 설명합니다.

## 📊 구조화된 지식 (Synthesized Content)
- **도시 명칭**: 초자동화 영상 생산 도시 (Automated Video Production City)
- **핵심 기술 스택**: React (Frontend), FastAPI (Backend), Gemini 3 & Veo 3.1 (AI Models) 통합.
- **운영 철학**: 지진(데이터 불확실성), 자재(데이터 정확성), 지하 발전소(안정적인 API), 지상 랜드마크(직관적인 사용자 경험)로 소프트웨어 개념을 은유적으로 표현.
- **현재 공사 상황**: Gemini 3, Veo 3.1 통합 시스템 설계 중이며, 데이터 파이프라인 초기 스키마 정의 및 GCP API 키 보안 점검 필요.
- **백엔드 구현 (FastAPI)**: `Video Generation Gateway` 역할을 하며, `/generate` 엔드포인트를 통해 영상 생성 요청을 처리.
- **AI 서비스 구현 (Google AI)**: `vertexai`를 활용하여 Gemini-3-pro, Gemini-3-pro-image-preview, Veo-3.1-generate-preview 모델 로드. 4단계 공정 (시장 조사, 자재 준비, 합성 연구소, 방송국)으로 영상 생성 파이프라인을 구성.

## 🔗 지식 연결망 (Knowledge Connections)
- **Related Topics:** [[Generative AI]], [[Video Synthesis]], [[FastAPI]], [[React]], [[Vertex AI]], [[System Architecture]], [[API Design]], [[Data Pipelines]], [[Prompt Engineering]]
- **Projects/Contexts:** [[AI_City_Project]]
- **Contradictions/Notes:** AI 서비스 (`google_ai.py`) 내 `run_video_generation` 함수의 4단계 공정은 현재 `TODO` 주석으로 실제 로직이 구현되지 않은 플레이스홀더 상태입니다. 또한, Veo 3.1 모델은 코드에서 'Hypothetical Veo integration'으로 명시되어 있어, 실제 통합 여부 및 기능성이 확정되지 않았을 수 있습니다. `.env` 파일의 GCP 키 보안 점검은 '미확인' 상태로 언급되어 있어, 실제 운영 환경에서의 설정 유효성에 대한 추가 확인이 필요합니다.

updated: 2026-05-31
