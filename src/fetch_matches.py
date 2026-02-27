import sys
import json
import requests
import argparse
import time
from common import configure_logger, load_env, ServerRequestError

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["RIOT_API_KR_ROOT", "RIOT_API_KEY"])
RIOT_API_KR_ROOT = env.get("RIOT_API_KR_ROOT")
RIOT_API_KEY = env.get("RIOT_API_KEY")
RIOT_API_ASIA_ROOT = "https://asia.api.riotgames.com"

# JSON 형태로 결과가 저장될 경로
SUMMONER_MATCHES_FILE_PATH = "summoner_matches.json"

# constants
QUEUE = "RANKED_SOLO_5x5"
MAX_SUMMONERS = 200
MATCH_COUNT = 30
DIVISIONS = ["I", "II", "III", "IV"]


def get_summoner_puuids_high_tier(target_tier: str) -> list[str]:
    RIOT_API_URL = f"{RIOT_API_KR_ROOT}/lol/league/v4/{target_tier}leagues/by-queue/{QUEUE}?api_key={RIOT_API_KEY}"

    response = requests.get(RIOT_API_URL)

    if response.status_code != 200:
        raise ServerRequestError(
            f"API 요청 실패: {response.status_code} - {response.text}"
        )

    entries = response.json().get("entries", [])
    entries = entries[:MAX_SUMMONERS]

    return [entry["puuid"] for entry in entries if "puuid" in entry]


def get_summoner_puuids(target_tier: str) -> list[str]:
    result_puuids = []

    for division in DIVISIONS:
        RIOT_API_URL = f"{RIOT_API_KR_ROOT}/lol/league/v4/entries/{QUEUE}/{target_tier}/{division}?api_key={RIOT_API_KEY}"

        response = requests.get(RIOT_API_URL)

        if response.status_code != 200:
            raise ServerRequestError(
                f"API 요청 실패: {response.status_code} - {response.text}"
            )

        entries = response.json()

        # 각 division별로 나누어 추출
        result_puuids.extend(
            [entry["puuid"] for entry in entries[: (MAX_SUMMONERS // len(DIVISIONS))]]
        )

    return result_puuids


def fetch_recent_match_ids(puuid: str) -> list[str]:
    queues = [420, 440]
    match_ids = set()

    for queue in queues:
        url = f"{RIOT_API_ASIA_ROOT}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={MATCH_COUNT}&queue={queue}&api_key={RIOT_API_KEY}"

        retries = 3
        for i in range(retries):
            res = requests.get(url)
            if res.status_code == 200:
                match_ids.update(res.json())
                break
            elif res.status_code == 429:
                retry_after = int(res.headers.get("Retry-After", 2))
                logger.warning(
                    f"요청 한도 초과 (PUUID {puuid}, queue {queue}). {retry_after}초 대기 후 재시도..."
                )
                time.sleep(retry_after)
            else:
                logger.error(
                    f"매치 아이디 가져오기 실패 (PUUID: {puuid}, Queue: {queue}): {res.status_code} - {res.text}"
                )
                break

    return list(match_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="소환사 매치 ID 가져오기")
    parser.add_argument(
        "--tier",
        type=str,
        choices=[
            "master",
            "grandmaster",
            "challenger",
            "diamond",
            "emerald",
            "platinum",
            "gold",
            "silver",
            "bronze",
            "iron",
        ],
        help="가져올 소환사가 소속된 티어",
        required=True,
    )

    target_tier = parser.parse_args().tier

    # 챌린저, 그랜드마스터, 마스터 티어는 별도로 처리
    if target_tier in ["master", "grandmaster", "challenger"]:
        puuids = get_summoner_puuids_high_tier(target_tier)
    # 나머지 티어 처리
    else:
        target_tier = target_tier.upper()
        puuids = get_summoner_puuids(target_tier)

    puuid_match_map = {}
    failed_puuids = []

    logger.info(f"총 {len(puuids)}명의 소환사 PUUID 발견. 매치 ID 수집 시작...")

    for i, puuid in enumerate(puuids):
        try:
            matches = fetch_recent_match_ids(puuid)
            puuid_match_map[puuid] = matches
            logger.info(
                f"[{i + 1}/{len(puuids)}] {puuid}: 매치 {len(matches)}개 수집 완료"
            )
        except Exception as e:
            logger.error(f"PUUID {puuid} 매치 수집 중 에러 발생: {e}")
            failed_puuids.append(puuid)

    # 결과를 json으로 저장
    with open(SUMMONER_MATCHES_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(puuid_match_map, f, indent=4, ensure_ascii=False)

    logger.info(
        f"{SUMMONER_MATCHES_FILE_PATH} 에 총 {len(puuid_match_map)}명 유저의 데이터 저장 완료."
    )

    if failed_puuids:
        logger.error(f"매치 수집 실패한 PUUID 목록: {', '.join(failed_puuids)}")

    if len(failed_puuids) > 3:
        sys.exit(1)
