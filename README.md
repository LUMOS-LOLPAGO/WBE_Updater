# 롤파고 업데이트

롤파고 관련 데이터를 주기적으로 업데이트하는 Python 기반 자동화 프로젝트

---

## 기술 스택

- **Python** 3.10
- **uv** — 패키지 및 프로젝트 관리
- **GitHub Actions** — 스케줄링 및 CI/CD
- **Ruff** — 코드 포매팅 및 린팅

---

## 프로젝트 구조

```
├── .github/workflows/       # GitHub Actions 워크플로우
├── src/
│   ├── common.py                          # 공통 유틸리티 (로거, 환경변수 로드)
│   ├── add_summoners.py                   # 상위 소환사 일괄 추가
│   ├── add_tier_summoners.py              # 특정 디비전 소환사 추가
│   ├── fetch_matches.py                   # 티어별 매치 ID 수집
│   ├── update_statistics.py               # 매치 통계 업데이트
│   ├── update_active_summoner_records.py   # 활성 소환사 전적 업데이트
│   ├── update_relative_winrate.py         # 상대승률 업데이트
│   ├── update_stale_summoners.py          # 오래된 소환사 정보 갱신
│   └── update_static_data.py             # 정적 데이터 업데이트
└── tests/                   # 테스트
```

---

## 시작하기

### 사전 요구사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

### 설치

```bash
uv sync --locked
```

### 환경 변수

로컬 개발환경에서는 `.env` 파일로, GitHub Actions에서는 GitHub Secrets로 관리합니다.

| 변수명             | 설명                                                   |
| ------------------ | ------------------------------------------------------ |
| `RIOT_API_KR_ROOT` | Riot API 루트 URL (예: `https://kr.api.riotgames.com`) |
| `RIOT_API_KEY`     | Riot API Key                                           |
| `SERVER_URL`       | 내부 API 서버 주소                                     |

---

## 수동 실행

```bash
# 티어별 매치 수집 → 통계 업데이트
uv run src/fetch_matches.py --tier challenger
uv run src/update_statistics.py

# 상위 소환사 일괄 추가
uv run src/add_summoners.py

# 특정 디비전 소환사 추가
uv run src/add_tier_summoners.py --tier DIAMOND --division I

# 상대승률 업데이트
uv run src/update_relative_winrate.py

# 활성 소환사 전적 업데이트
uv run src/update_active_summoner_records.py

# 오래된 소환사 정보 갱신
uv run src/update_stale_summoners.py

# 정적 데이터 업데이트
uv run src/update_static_data.py
```

---

## 코드 품질

```bash
uv run ruff format .   # 포매팅
uv run ruff check .    # 린트
pytest                 # 테스트
```

---

## 운영 스케줄 (GitHub Actions)

모든 워크플로우는 `workflow_dispatch`를 통해 수동 실행도 가능합니다.

| 워크플로우                  | 실행 주기               | 설명                                                                                                  |
| --------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------- |
| 티어별 매치 통계 업데이트   | 매일 01:00 (KST)        | 아이언~챌린저 전 티어, 티어별 200명 대상. 상위→중위→하위 순차 실행                                    |
| 상대승률 업데이트           | 매일 02:00 (KST)        | 전 티어 대상 상대승률 계산                                                                            |
| 상위 소환사 일괄 추가       | 매일 03:00 (KST)        | 챌린저·그랜드마스터·마스터 소환사 PUUID 수집 후 서버 등록. 기존 소환사 정보 갱신 포함                  |
| 오래된 소환사 정보 갱신     | 매일 04:00 (KST)        | 가장 오래 갱신되지 않은 소환사부터 순차 처리. Riot API에 없는 소환사는 삭제                            |
| 활성 소환사 전적 업데이트   | 매 1시간 (정각)         | 소환사 최신 정보 갱신 후 전적 업데이트. Riot API에 없는 소환사는 삭제 후 생략                          |
| 정적 데이터 업데이트        | 매주 월요일 00:00 (KST) | DDragon 기반 챔피언·아이템·룬·스킬·스펠 정보 갱신                                                     |
| 특정 디비전 소환사 일괄 추가 | 수동 실행 전용          | 다이아몬드 이하 특정 티어+디비전의 소환사를 수동 추가                                                 |
| 특정 티어 통계 업데이트     | 수동 실행 전용          | 원하는 티어의 매치 수집 및 통계 업데이트                                                              |
