import argparse
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
DIVISIONS = ["I", "II", "III", "IV"]


def get_puuids_regular_tier(tier: str, division: str) -> list[str]:
    all_puuids = []

    page = 1
    while True:
        url = (
            f"{RIOT_API_KR_ROOT}/lol/league/v4/entries/{QUEUE}/{tier}/{division}"
            f"?page={page}&api_key={RIOT_API_KEY}"
        )

        retries = 10
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
            raise ServerRequestError(f"재시도 횟수 초과 ({tier} {division} page {page})")

        entries = response.json()
        if not entries:
            break

        puuids = [entry["puuid"] for entry in entries if "puuid" in entry]
        all_puuids.extend(puuids)
        page += 1

    logger.info(f"{tier} {division}: 총 {len(all_puuids)}명")

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
            raise ServerRequestError(f"소환사 추가 실패: {res.status_code} - {res.text}")

    raise ServerRequestError("재시도 횟수 초과")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="특정 디비전 소환사 일괄 추가")
    parser.add_argument(
        "--tier",
        type=str,
        choices=[
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
        required=True,
        help="추가할 디비전",
    )
    parser.add_argument(
        "--chunk-index",
        type=int,
        default=0,
        help="처리할 청크 인덱스 (0부터 시작)",
    )
    parser.add_argument(
        "--total-chunks",
        type=int,
        default=1,
        help="전체 청크 수",
    )
    args = parser.parse_args()
    tier = args.tier
    division = args.division
    chunk_index = args.chunk_index
    total_chunks = args.total_chunks

    logger.info(f"{tier} {division} 소환사 목록 조회 중...")
    puuids = get_puuids_regular_tier(tier, division)

    # 청크 분할
    chunk_size = len(puuids) // total_chunks
    start = chunk_index * chunk_size
    end = len(puuids) if chunk_index == total_chunks - 1 else start + chunk_size
    chunk_puuids = puuids[start:end]

    logger.info(
        f"총 {len(puuids)}명 중 청크 {chunk_index + 1}/{total_chunks} "
        f"({len(chunk_puuids)}명, 인덱스 {start}~{end - 1}) 등록 시작..."
    )

    created = 0
    already_exists = 0
    failed = 0

    for i, puuid in enumerate(chunk_puuids):
        try:
            result = add_summoner(puuid)
            if result["status"] == "created":
                created += 1
            else:
                already_exists += 1
        except Exception as e:
            failed += 1
            logger.error(f"[{i + 1}/{len(chunk_puuids)}] 실패 (puuid: {puuid}): {e}")

        if (i + 1) % 1000 == 0 or (i + 1) == len(chunk_puuids):
            logger.info(
                f"[{i + 1}/{len(chunk_puuids)}] 진행 중 - "
                f"신규: {created}, 이미 존재: {already_exists}, 실패: {failed}"
            )

    logger.info(f"완료 - 신규: {created}, 이미 존재: {already_exists}, 실패: {failed}")
