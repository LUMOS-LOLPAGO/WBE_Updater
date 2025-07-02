# 소환사 전적 업데이트

소환사 정보를 자동으로 수집하고, 소환사 전적 데이터를 주기적으로 업데이트하는 Python 기반 자동화 프로젝트

---

## 현재 운영 정보
- 대상 소환사 : 챌린저 리그에 소속된 소환사
- 실행 주기 : github actions, 09:00, 13:00 (KST)

---

##  환경 변수

- Github Actions에 사용되는 환경 변수는 GitHub Secrets를 통해 관리.
- 로컬 개발환경에서는 .env 파일로 관리.

| 변수명 | 설명 |
|--------|------|
| `RIOT_API_KR_ROOT` | Riot API 루트 URL (예: `https://kr.api.riotgames.com`) |
| `RIOT_API_KEY` | Riot API Key |
| `SERVER_URL` | 소환사 및 전적 저장을 위한 내부 API 서버 주소 |
| `SUMMONER_ID_FILE_PATH` | 저장할 소환사 ID 파일 경로 (`summoner_ids.txt`) |
