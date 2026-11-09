# develof-static

DEVELOF 사이트(gulbi.develof.com, flower.develof.com 등)의 **빌드 완성본** 보관소. 소스 코드 없음.

한국 방문자에게 Cloudflare 무료 경로가 미국(LAX·SEA)을 거쳐 느린 문제 회피용. 무거운 파일(앱 본체, 사진, 글꼴)을 jsDelivr 서울(ICN) 경유로 전달.

- `<사이트>/<버전>/main.dart.<해시>.js`, `<사이트>/<버전>/assets/...`
- 배포: 각 사이트 빌드 후 `python publish.py <사이트> <build/web>` - 새 버전 폴더 커밋·push 후 사이트의 `flutter_bootstrap.js` 에 jsDelivr 주소(커밋 SHA 고정) 기록
- jsDelivr 가 응답하지 않으면 사이트 서버의 같은 파일로 자동 대체
