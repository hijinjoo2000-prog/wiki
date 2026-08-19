# trend_sniper.py
def fetch_trend_data(query: str) -> dict:
    """검색어 기반 트렌드 데이터 수집 (가상 구현)"""
    return {"query": query, "trend_score": 95.2}

# pytest 테스트 케이스
def test_fetch_trend_data():
    result = fetch_trend_data("부동산")
    assert "query" in result
    assert "trend_score" in result
    assert 0 <= result["trend_score"] <= 100