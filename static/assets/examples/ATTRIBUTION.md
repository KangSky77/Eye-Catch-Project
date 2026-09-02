# 촬영 예시 이미지 출처

`face-good.jpg`(좋은 예)와 `face-blurry.jpg`(흔들린 예)는 아래 한 장을 가공한 것입니다.

| 파일 | 원본 | 저작자 | 라이선스 |
|---|---|---|---|
| face-good.jpg, face-blurry.jpg | [File:Face portrait (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Face_portrait_(Unsplash).jpg) (Wikimedia Commons, 원출처 Unsplash) | William Stitt | CC0 1.0 (퍼블릭 도메인 헌정) |

- 가공 내용: 1280px 축소본을 4:3으로 얼굴 중심 크롭 → 480x360 축소. 흔들린 예는 가로 손떨림(44px 모션 블러) + 가우시안 4px를 더한 것으로,
  실제 서버 파이프라인(MTCNN 눈 크롭 → 흔들림 게이트)에 넣으면 `blurry`로 재촬영 안내가 나오는 강도다(2026-09-02 확인).
- CC0이라 표기 의무는 없지만, 질환 사진(`../diseases/ATTRIBUTION.md`)과 같은 기준으로 출처를 남깁니다.
