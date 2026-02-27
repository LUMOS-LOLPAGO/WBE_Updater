import sys
import time
import requests
from common import configure_logger, load_env

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["SERVER_URL"])
SERVER_URL = env.get("SERVER_URL")

MAX_RETRIES = 3


def fetch_active_summoner_ids() -> list[str]:
    url = f"{SERVER_URL}/summoners/active?limit=100"
    res = requests.get(url)
    res.raise_for_status()
    return res.json()["summonerIds"]


def update_active_summoner_records(summoner_ids: list[str]) -> tuple[int, int, int]:
    success_count = 0
    skipped_count = 0
    failure_count = 0
    retries = 0

    for summoner_id in summoner_ids:
        try:
            refresh_res = requests.post(f"{SERVER_URL}/summoners/{summoner_id}/refresh")

            if refresh_res.status_code == 204:
                skipped_count += 1
                retries = 0
                logger.info(
                    f"[스킵:{skipped_count}] {summoner_id} - 소환사 정보 없음 (삭제됨)"
                )
                continue
            elif refresh_res.status_code == 200:
                logger.info(f"[갱신성공] {summoner_id} - 소환사 정보 최신화 완료")
            else:
                logger.warning(
                    f"[갱신실패] {summoner_id} - {refresh_res.status_code} {refresh_res.text}"
                )

            res = requests.post(
                f"{SERVER_URL}/matches/update",
                json={"summonerId": summoner_id},
            )

            if res.status_code == 200:
                success_count += 1
                retries = 0
                data = res.json()
                logger.info(f"[성공:{success_count}] {summoner_id} - {data}")
            elif res.status_code == 204:
                skipped_count += 1
                retries = 0
                logger.info(f"[스킵:{skipped_count}] {summoner_id} - 업데이트 불필요")
            else:
                failure_count += 1
                retries = 0
                logger.error(
                    f"[실패:{failure_count}] {summoner_id} - "
                    f"{res.status_code} {res.text}"
                )

        except requests.exceptions.ConnectionError:
            retries += 1
            failure_count += 1
            if retries >= MAX_RETRIES:
                logger.error(f"서버 연결 실패 {MAX_RETRIES}회 연속 - 중단합니다.")
                break
            logger.warning(f"연결 실패 ({retries}/{MAX_RETRIES}) - 3초 후 재시도...")
            time.sleep(3)

        except requests.exceptions.HTTPError as e:
            failure_count += 1
            retries = 0
            logger.error(f"HTTP 에러: {e}")
            time.sleep(1)

        except Exception as e:
            failure_count += 1
            retries = 0
            logger.error(f"에러: {e}")
            time.sleep(1)

    return success_count, skipped_count, failure_count


if __name__ == "__main__":
    summoner_ids = fetch_active_summoner_ids()
    logger.info(f"활성 소환사 {len(summoner_ids)}명 전적 업데이트 시작")

    success, skipped, failures = update_active_summoner_records(summoner_ids)
    logger.info(f"완료 | 성공: {success}건, 스킵: {skipped}건, 실패: {failures}건")

    if failures > 0:
        sys.exit(1)
