import sys
import requests
import argparse
from common import configure_logger, load_env, ServerRequestError

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(
    ["RIOT_API_KR_ROOT", "RIOT_API_KEY", "SERVER_URL", "SUMMONER_ID_FILE_PATH"]
)
RIOT_API_KR_ROOT = env.get("RIOT_API_KR_ROOT")
RIOT_API_KEY = env.get("RIOT_API_KEY")
SERVER_URL = env.get("SERVER_URL")
SUMMONER_ID_FILE_PATH = env.get("SUMMONER_ID_FILE_PATH")

# constants
QUEUE = "RANKED_SOLO_5x5"
REGION = "KR"
MAX_SUMMONERS = 300


def request_upsert_summoner(entry: dict) -> tuple[str, str]:
    puuid = entry.get("puuid")
    body = {"puuid": puuid, "region": REGION}
    res = requests.post(f"{SERVER_URL}/summoners", json=body)
    status_code = res.status_code

    if status_code not in [201, 409]:
        raise ServerRequestError(f"{puuid} 실패: {status_code} - {res.text}")

    data = res.json()
    return (
        data["id"],
        f"{data['name']}#{data['tag']} (PUUID: {puuid}, ID: {data['id']}) 저장 완료",
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="소환사 ID 가져오기")
    parser.add_argument(
        "--tier",
        type=str,
        choices=["master", "grandmaster", "challenger"],
        help="가져올 소혼사가 소속된 티어",
        required=True,
    )

    target_tier = parser.parse_args().tier

    RIOT_API_URL = f"{RIOT_API_KR_ROOT}/lol/league/v4/{target_tier}leagues/by-queue/{QUEUE}?api_key={RIOT_API_KEY}"

    response = requests.get(RIOT_API_URL)
    entries = response.json().get("entries", [])
    entries = entries[:MAX_SUMMONERS]

    success_ids = []
    failed_puuids = []

    for entry in entries:
        try:
            summoner_id, result_message = request_upsert_summoner(entry)
            logger.info(result_message)
            success_ids.append(summoner_id)
        except ServerRequestError as e:
            logger.error(f"소환사 정보 저장 실패: {e}")
            failed_puuids.append(entry.get("puuid"))

    # ID들을 jsonl로 저장
    with open(SUMMONER_ID_FILE_PATH, "w", encoding="utf-8") as f:
        for sid in success_ids:
            f.write(f"{sid}\n")

    if failed_puuids:
        logger.error(f"실패한 PUUID 목록: {', '.join(failed_puuids)}")
        sys.exit(1)
