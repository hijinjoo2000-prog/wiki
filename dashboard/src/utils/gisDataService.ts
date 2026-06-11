/**
 * @fileoverview GeoJSON FeatureCollection을 React Native Map Component가 사용할 수 있는 렌더링 데이터 배열로 변환하는 서비스 레이어.
 */

import { Feature } from 'geojson';

// 네이버 지도에서 요구하는 좌표 타입 정의 (latitude, longitude)
export type Coordinate = { latitude: number; longitude: number };

// GeoJSON의 모든 Feature를 처리하여 Polygon 렌더링에 필요한 데이터를 추출합니다.
/**
 * @param geojsonData - 외부로부터 로드된 GeoJSON FeatureCollection 객체.
 * @returns {Array<{ coordinates: Coordinate[][], properties: any }>} Map 컴포넌트가 소비할 준비된 데이터 배열.
 */
export const parseGeojsonFeatures = (geojsonData: { type: 'FeatureCollection', features: Feature[] }): Array<{ coordinates: Coordinate[][], properties: any }> => {
    if (!geojsonData || geojsonData.type !== "FeatureCollection") {
        console.error("Invalid GeoJSON data provided.");
        return [];
    }

    const parsedFeatures = geojsonData.features.map(feature => {
        // GeoJSON은 [경도, 위도] 순서이므로, 네이버 지도가 사용하는 [위도, 경도]로 변환합니다.
        if (!feature.geometry || feature.geometry.coordinates.length === 0) {
             console.warn("Feature missing geometry or coordinates.");
             return null;
        }

        // 첫 번째 좌표계(Polygon의 경우)를 가져옵니다.
        const rawCoordinates = feature.geometry.coordinates[0];
        
        if (!rawCoordinates) return null;

        // [경도, 위도] -> [{ latitude: 위도, longitude: 경도 }, ...] 변환 로직
        const coordinates: Coordinate[][] = rawCoordinates.map(coord => ({ 
            latitude: coord[1], // 위도 (Y축)
            longitude: coord[0] // 경도 (X축)
        }));

        return {
            coordinates: [coordinates], // Polygon은 좌표 배열의 배열 형태가 필요합니다.
            properties: feature.properties || {}
        };
    }).filter(Boolean) as Array<{ coordinates: Coordinate[][], properties: any }>;

    return parsedFeatures;
};

/**
 * 지도 렌더링에 필요한 모든 정보를 추출하는 메인 함수.
 * @param geojsonData GeoJSON FeatureCollection
 * @returns {Array<{ coords: Coordinate[], name: string, fill: string, stroke: string }>} 컴포넌트 전용 데이터 배열
 */
export const processMapData = (geojsonData: { type: 'FeatureCollection', features: Feature[] }) => {
    const renderedData = [];

    for (const feature of geojsonData.features) {
        if (!feature.geometry || !feature.properties) continue;

        // 1. Polygon 좌표 변환 및 추출
        const rawCoordinates = feature.geometry.coordinates[0];
        const polygonCoords: Coordinate[] = rawCoordinates.map(coord => ({ 
            latitude: coord[1], longitude: coord[0] 
        }));
        
        // 2. 렌더링 컴포넌트에 필요한 속성 추출
        renderedData.push({
            coords: polygonCoords,
            name: feature.properties.name || 'Unnamed Zone',
            fill: feature.properties.fillColor || 'rgba(255, 0, 0, 0.4)',
            stroke: feature.properties.strokeColor || '#CC0000'
        });
    }

    return renderedData;
};