# ortarot-marketing

오르타로 앱 마케팅 자동화 (앱 저장소 ortarot-app 과 분리).

- `instagram/posts/<날짜_번호_이름>/` : post.json(caption, images) + JPEG 이미지
- `.github/workflows/instagram-publish.yml` : 수동 실행. `check`(토큰 확인) / `publish`(confirm=POST)
- 토큰: Secret `INSTAGRAM_ACCESS_TOKEN` (값은 저장소·채팅에 남기지 않음)
