import sys
import time

import requests

from common import ServerRequestError, configure_logger, load_env

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["RIOT_API_KR_ROOT", "RIOT_API_KEY", "SERVER_URL"])
RIOT_API_KR_ROOT = env.get("RIOT_API_KR_ROOT")
RIOT_API_KEY = env.get("RIOT_API_KEY")
SERVER_URL = env.get("SERVER_URL")

QUEUE = "RANKED_SOLO_5x5"
REGION = "kr"
HIGH_TIERS = ["challenger", "grandmaster", "master"]


def get_all_puuids_high_tier(tier: str) -> list[str]:
    url = f"{RIOT_API_KR_ROOT}/lol/league/v4/{tier}leagues/by-queue/{QUEUE}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise ServerRequestError(
            f"Riot API 요청 실패 ({tier}): {response.status_code} - {response.text}"
        )

    entries = response.json().get("entries", [])
    return [entry["puuid"] for entry in entries if "puuid" in entry]


def refresh_summoner(summoner_id: str) -> None:
    url = f"{SERVER_URL}/summoners/{summoner_id}/refresh"
    res = requests.post(url)

    if res.status_code == 200:
        logger.info(f"소환사 정보 갱신 완료 (id: {summoner_id})")
    else:
        logger.warning(f"소환사 정보 갱신 실패 (id: {summoner_id}): {res.status_code} - {res.text}")


def add_summoner(puuid: str) -> dict:
    url = f"{SERVER_URL}/summoners"
    payload = {"puuid": puuid, "region": REGION}

    retries = 3
    for attempt in range(retries):
        res = requests.post(url, json=payload)

        if res.status_code == 201:
            data = res.json()
            refresh_summoner(data["summonerId"])
            return {"status": "created", "data": data}
        elif res.status_code == 409:
            data = res.json()
            refresh_summoner(data["summonerId"])
            return {"status": "already_exists", "data": data}
        elif res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", 5))
            logger.warning(f"요청 한도 초과. {retry_after}초 대기 후 재시도...")
            time.sleep(retry_after)
        else:
            raise ServerRequestError(f"소환사 추가 실패: {res.status_code} - {res.text}")

    raise ServerRequestError("재시도 횟수 초과")


if __name__ == "__main__":
    all_puuids = []

    for tier in HIGH_TIERS:
        logger.info(f"{tier} 티어 소환사 목록 조회 중...")
        puuids = get_all_puuids_high_tier(tier)
        logger.info(f"{tier}: {len(puuids)}명 발견")
        all_puuids.extend(puuids)

    logger.info(f"총 {len(all_puuids)}명의 소환사 등록 시작...")

    created = 0
    already_exists = 0
    failed = 0

    for i, puuid in enumerate(all_puuids):
        try:
            result = add_summoner(puuid)
            if result["status"] == "created":
                created += 1
            else:
                already_exists += 1
        except Exception as e:
            failed += 1
            logger.error(f"[{i + 1}/{len(all_puuids)}] 실패 (puuid: {puuid}): {e}")

        if (i + 1) % 1000 == 0 or (i + 1) == len(all_puuids):
            logger.info(
                f"[{i + 1}/{len(all_puuids)}] 진행 중 - "
                f"신규: {created}, 이미 존재: {already_exists}, 실패: {failed}"
            )

    logger.info(f"완료 - 신규: {created}, 이미 존재: {already_exists}, 실패: {failed}")

    if failed > 3:
        sys.exit(1)
