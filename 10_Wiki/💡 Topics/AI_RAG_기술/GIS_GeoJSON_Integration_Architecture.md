---
# 🗺️ GIS 데이터 GeoJSON 통합 아키텍처 (Location Intelligence)

## 🎯 목표: 정적 이미지에서 동적, 지능형 지도로의 전환
이 문서는 단순 시각화(Visualization)를 넘어, 실제 지리 공간 데이터를 활용하여 지식 콘텐츠에 위치 정보와 시간 변화라는 '차원'을 부여하는 아키텍처 설계도를 담고 있습니다.

## ⚙️ 데이터 흐름 (Data Flow Pipeline)
1. **Source Layer:** 공공데이터 포털 또는 GIS 전문 DB에서 정비구역 경계(GeoJSON), 지하철 노선(LineString GeoJSON), 개발 계획 구역(Polygon GeoJSON)을 확보합니다.
2. **Preprocessing Layer (Backend):** 수신된 Raw GeoJSON 데이터를 파싱하고, 해당 좌표에 대한 메타데이터 (예: `재개발_유형`, `용도지역`, `최대층수`)를 연결하여 구조화합니다.
3. **API Service Layer:** 클라이언트(React Native)가 요청하는 지역(`Bounding Box` 기반)을 기준으로 필터링된 GeoJSON 데이터를 제공합니다.
4. **Presentation Layer (Frontend):** Naver/Google Map SDK에서 Polygon, Path 등의 네이티브 컴포넌트를 사용하여 시각화하고, 각 폴리곤 위에 연결된 메타데이터를 통해 라벨 카드(`Marker`)를 띄웁니다.

## ✨ 핵심 기술적 요소
*   **GeoJSON 활용:** 복잡한 다각형 경계를 정의하는 표준 형식입니다. 반드시 모든 구역 경계는 GeoJSON의 `Polygon` 또는 `MultiPolygon` 구조로 관리되어야 합니다.
*   **데이터 레이어 분리:** 지형(River/Park) 데이터, 인프라(Road/Subway) 데이터, 프로젝트 구역(Redevelopment Zone) 데이터를 완전히 별도의 레이어로 분리하여 처리해야 성능 최적화가 가능합니다.
*   **성능 관리:** 지도 뷰의 변경 이벤트 (`onViewChange`) 발생 시 불필요한 재렌더링을 방지하는 로직 구현이 필수입니다.

## 💡 활용 가치 (Knowledge Value)
단순히 '어디에 있다'를 넘어, **'왜 이 구역에 어떤 규제가 적용되는가?'**라는 논리적 질문(규제 메타데이터)을 지도 위에 오버레이하여 사용자에게 제공할 수 있습니다.

---
updated: 2024-06-19