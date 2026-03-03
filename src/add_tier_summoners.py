import time
import argparse
import requests
from common import configure_logger, load_env, ServerRequestError

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["RIOT_API_KR_ROOT", "RIOT_API_KEY", "SERVER_URL"])
RIOT_API_KR_ROOT = env.get("RIOT_API_KR_ROOT")
RIOT_API_KEY = env.get("RIOT_API_KEY")
SERVER_URL = env.get("SERVER_URL")

QUEUE = "RANKED_SOLO_5x5"
REGION = "kr"
HIGH_TIERS = ["challenger", "grandmaster", "master"]
DIVISIONS = ["I", "II", "III", "IV"]


def get_puuids_high_tier(tier: str) -> list[str]:
    url = f"{RIOT_API_KR_ROOT}/lol/league/v4/{tier}leagues/by-queue/{QUEUE}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise ServerRequestError(
            f"Riot API 요청 실패 ({tier}): {response.status_code} - {response.text}"
        )

    entries = response.json().get("entries", [])
    return [entry["puuid"] for entry in entries if "puuid" in entry]


def get_puuids_regular_tier(tier: str, division: str | None = None) -> list[str]:
    all_puuids = []
    divisions = [division] if division else DIVISIONS

    for division in divisions:
        page = 1
        while True:
            url = (
                f"{RIOT_API_KR_ROOT}/lol/league/v4/entries/{QUEUE}/{tier}/{division}"
                f"?page={page}&api_key={RIOT_API_KEY}"
            )

            retries = 3
            response = None
            for attempt in range(retries):
                response = requests.get(url)
                if response.status_code == 200:
                    break
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"요청 한도 초과. {retry_after}초 대기 후 재시도...")
                    time.sleep(retry_after)
                else:
                    raise ServerRequestError(
                        f"Riot API 요청 실패 ({tier} {division} page {page}): "
                        f"{response.status_code} - {response.text}"
                    )

            if response is None or response.status_code != 200:
                raise ServerRequestError(
                    f"재시도 횟수 초과 ({tier} {division} page {page})"
                )

            entries = response.json()
            if not entries:
                break

            puuids = [entry["puuid"] for entry in entries if "puuid" in entry]
            all_puuids.extend(puuids)
            page += 1

        logger.info(f"{tier} {division}: 누적 {len(all_puuids)}명")

    return all_puuids


def add_summoner(puuid: str) -> dict:
    url = f"{SERVER_URL}/summoners"
    payload = {"puuid": puuid, "region": REGION}

    retries = 3
    for attempt in range(retries):
        res = requests.post(url, json=payload)

        if res.status_code == 201:
            return {"status": "created", "data": res.json()}
        elif res.status_code == 409:
            return {"status": "already_exists", "data": res.json()}
        elif res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", 5))
            logger.warning(f"요청 한도 초과. {retry_after}초 대기 후 재시도...")
            time.sleep(retry_after)
        else:
            raise ServerRequestError(
                f"소환사 추가 실패 (puuid: {puuid}): {res.status_code} - {res.text}"
            )

    raise ServerRequestError(f"재시도 횟수 초과 (puuid: {puuid})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="특정 티어 소환사 일괄 추가")
    parser.add_argument(
        "--tier",
        type=str,
        choices=[
            "challenger",
            "grandmaster",
            "master",
            "DIAMOND",
            "EMERALD",
            "PLATINUM",
            "GOLD",
            "SILVER",
            "BRONZE",
            "IRON",
        ],
        required=True,
        help="추가할 소환사의 티어",
    )
    parser.add_argument(
        "--division",
        type=str,
        choices=DIVISIONS,
        default=None,
        help="특정 디비전만 처리 (일반 티어 전용)",
    )
    args = parser.parse_args()
    tier = args.tier
    division = args.division

    # 소환사 PUUID 수집
    if tier in HIGH_TIERS:
        logger.info(f"{tier} 티어 소환사 목록 조회 중...")
        puuids = get_puuids_high_tier(tier)
    else:
        label = f"{tier} {division}" if division else f"{tier} 전 디비전"
        logger.info(f"{label} 소환사 목록 조회 중...")
        puuids = get_puuids_regular_tier(tier, division)

    logger.info(f"총 {len(puuids)}명의 소환사 등록 시작...")

    created = 0
    already_exists = 0
    failed = 0

    for i, puuid in enumerate(puuids):
        try:
            result = add_summoner(puuid)
            if result["status"] == "created":
                created += 1
            else:
                already_exists += 1
        except Exception as e:
            failed += 1
            logger.error(f"[{i + 1}/{len(puuids)}] 실패 (puuid: {puuid}): {e}")

        if (i + 1) % 1000 == 0 or (i + 1) == len(puuids):
            logger.info(
                f"[{i + 1}/{len(puuids)}] 진행 중 - 신규: {created}, 이미 존재: {already_exists}, 실패: {failed}"
            )

    logger.info(
        f"완료 - 신규: {created}, 이미 존재: {already_exists}, 실패: {failed}"
    )
