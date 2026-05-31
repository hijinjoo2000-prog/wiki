---
id: e78b2734-d3a1-432a-bc91-2a1cb5b9f71c
category: "[[10_Wiki/🛠️ Projects]]"
confidence_score: 0.95
tags: ["AI_City", "Master_Plan", "FastAPI", "Veo", "Gemini"]
last_reinforced: 2026-05-31
github_commit: "1f08aeff3019f3df8cf9c4b23161983524fd05d8"
---

# [[AI_City_Master_Plan]]

## 📌 한 줄 포착 (The Karpathy Summary)
> 초자동화 영상 생산 도시(Automated Video Production City)를 구축하기 위해 React, FastAPI, Gemini 3, Veo 3.1 통합 기술 스택을 기반으로 한 시스템 설계 도면 및 데이터 파이프라인의 핵심 설계도입니다.

## 📊 구조화된 지식 (Synthesized Content)
- **도시 개요**:
  - **도시 이름**: 초자동화 영상 생산 도시 (Automated Video Production City)
  - **핵심 기술 스택**: React + FastAPI, Gemini 3 & Veo 3.1 통합
  - **운영 철학**: 지진(에러)은 데이터 불확실성, 자재는 데이터의 정확성, 지하 발전소(Backend)는 안정적인 API, 지상 랜드마크(Frontend)는 직관적인 사용자 경험 제공.
- **현재 공사 상황 (Protocol 0: Groundbreaking)**:
  - Gemini 3, Veo 3.1 통합 시스템 설계 중.
  - 데이터 파이프라인 상태: 초기 스키마 정의 단계.
  - 보안 점검: `.env` 파일에 `GCP_API_KEY`와 `GCP_PROJECT_ID` 존재 여부 확인 필요 (현재 미확인).
- **공사 진행 로그 (Build Log)**:
  - 초기 설계 완료. 다음 단계는 지하 발전소(FastAPI Backend)의 심장 구축입니다.
- **프로젝트 소스 설계**:
  - **GCP 설정 (`AI_City_Project/.env`)**:
    - `GCP_API_KEY` 및 `GCP_PROJECT_ID` 탑재 필요.
  - **FastAPI 게이트웨이 (`AI_City_Project/backend/main.py`)**:
    - 비동기 영상 생성 요청 API 제공 (`/generate`).
  - **구글 AI 서비스 (`AI_City_Project/backend/services/google_ai.py`)**:
    - Vertex AI 모듈 초기화.
    - `gemini-3-pro`, `veo-3.1-generate-preview` 가상 모델 바인딩.
    - 4단계 영상 생성 파이프라인(시장 조사 -> 자재 준비 -> 합성 연구소 -> 방송국 송출) 구현 Blueprint 설계.

## 🔗 지식 연결망 (Knowledge Connections)
- **Related Topics:** [[노량진뉴타운_자동화_SEO_시스템_설계보고서]], [[V11_Beta_투트랙_파이프라인_마스터스킬]]
- **Projects/Contexts:** 없음
- **Contradictions/Notes:** Vertex AI 초기화 시 실인증 실패 예외처리(try-except)가 되어 있으나 실제 API Key 주입 검증이 필수적임.

updated: 2026-05-31
