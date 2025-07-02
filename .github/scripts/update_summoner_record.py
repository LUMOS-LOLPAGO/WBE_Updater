import sys
import requests
from common import configure_logger, load_env, ServerRequestError

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["SERVER_URL", "SUMMONER_ID_FILE_PATH"])
SERVER_URL = env.get("SERVER_URL")
SUMMONER_ID_FILE_PATH = env.get("SUMMONER_ID_FILE_PATH")


def update_summoner_record(summoner_id: str) -> str:
    url = f"{SERVER_URL}/matches/update"
    res = requests.post(url, json={"summonerId": summoner_id})
    if res.status_code != 200:
        raise ServerRequestError(f"{summoner_id} 실패: {res.status_code} - {res.text}")
    return f"summoner_id:{summoner_id} 전적 업데이트 완료"


if __name__ == "__main__":

    failed_ids = []
    summoner_ids = []

    # 파일에서 소환사 ID 읽기
    try:
        with open(SUMMONER_ID_FILE_PATH, "r") as file:
            for line in file:
                sid = line.strip()
                if sid:
                    summoner_ids.append(sid)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {SUMMONER_ID_FILE_PATH}")
        sys.exit(1)

    # 소환사 전적 업데이트
    for summoner_id in summoner_ids:
        try:
            result_message = update_summoner_record(summoner_id)
            logger.info(result_message)
        except ServerRequestError as e:
            logger.error(f"전적 업데이트 실패: {e}")
            failed_ids.append(summoner_id)

    # 실패 요약 출력
    if failed_ids:
        logger.error(f"전적 업데이트 실패한 소환사 ID 목록: {', '.join(failed_ids)}")
        sys.exit(1)
    else:
        logger.info("모든 소환사 전적 업데이트 완료")
