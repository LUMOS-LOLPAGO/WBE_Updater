import sys
import requests
import json
from common import configure_logger, load_env, ServerRequestError

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["SERVER_URL"])
SERVER_URL = env.get("SERVER_URL")

TIER_LIST = [
    "IRON",
    "BRONZE",
    "SILVER",
    "GOLD",
    "PLATINUM",
    "DIAMOND",
    "MASTER",
    "GRANDMASTER",
    "CHALLENGER",
]


def update_relative_winrate(tier: str) -> str:
    url = f"{SERVER_URL}/relative-winrate/{tier}"
    res = requests.put(url)
    if res.status_code != 200:
        raise ServerRequestError(
            f"{tier} 티어 상대승률 업데이트 실패: {res.status_code} - {res.text}"
        )
    return str(json.loads(res.text))


if __name__ == "__main__":
    failed_tiers = []
    for tier in TIER_LIST:
        try:
            result_message = update_relative_winrate(tier)
            logger.info(result_message)
        except ServerRequestError as e:
            logger.error(e)
            failed_tiers.append(tier)

    if failed_tiers:
        sys.exit(1)
