from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# Pydantic 모델을 사용하여 데이터의 스키마를 강제합니다. (매우 중요)
class WikiArticleData(BaseModel):
    """WikiParser가 생성한 구조화된 아티클 데이터를 받을 모델."""
    metadata: Dict[str, Any]
    summary: str
    core_concepts: str
    deep_dive_analysis: str
    connectivity_action: str

app = FastAPI(
    title="Seropro Knowledge Wiki API",
    description="자동 분석 파이프라인의 최종 수신 엔드포인트입니다. 모든 지식 아티팩트는 이 API를 통해 저장됩니다."
)


@app.post("/api/v1/wiki/article")
async def save_new_article(data: WikiArticleData):
    """새로운 구조화된 위키 아티클을 데이터베이스에 저장합니다."""
    # TODO: 실제 DB 로직 (예: SQLAlchemy를 사용한 트랜잭션 커밋)이 들어갈 곳입니다.
    print("-----------------------------------------------------")
    print(f"💾 [DB] 성공적으로 '{data.metadata['title']}' 아티클을 데이터베이스에 저장했습니다.")
    print("   [Meta Info]: Source:", data.metadata['source_link'])
    # print(json.dumps(data.dict(), indent=2, ensure_ascii=False)) # 실제 디버깅 시 주석 해제
    print("-----------------------------------------------------")

    return {"status": "success", "message": f"Article '{data.metadata['title']}' saved successfully."}


@app.get("/api/v1/wiki/article/{slug}")
async def get_article(slug: str):
    """특정 슬러그로 아티클을 검색합니다."""
    # TODO: DB 조회 로직 구현
    if slug == "example-missing":
        raise HTTPException(status_code=404, detail="Article not found.")
    return {"article_id": 123, "title": f"Retrieved article for {slug}"}

print("✅ FastAPI 백엔드 API 서버 정의 완료. 포트 8000에서 구동 가능합니다.")