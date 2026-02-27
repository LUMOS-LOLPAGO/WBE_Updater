import sys
import time
import requests
from common import configure_logger, load_env

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["SERVER_URL"])
SERVER_URL = env.get("SERVER_URL")

URL = f"{SERVER_URL}/summoners/update-stale"
MAX_RETRIES = 3
DEFAULT_LIMIT = 1000


def update_stale_summoners(limit: int) -> tuple[int, int, int]:
    updated = 0
    deleted = 0
    errors = 0
    retries = 0

    for _ in range(limit):
        try:
            res = requests.post(URL)

            if res.status_code == 404:
                logger.info("더 이상 업데이트할 소환사가 없습니다.")
                break

            if res.status_code == 204:
                deleted += 1
                retries = 0
                logger.info(f"[삭제] 소환사가 삭제되었습니다. (총 {deleted}건)")
                continue

            res.raise_for_status()
            data = res.json()
            updated += 1
            retries = 0
            logger.info(
                f"[{updated}] [{data['name']}#{data['tag']}] "
                f"{data['staleDays']}일 경과 | {data['previousUpdatedDate']}"
            )

        except requests.exceptions.ConnectionError:
            retries += 1
            errors += 1
            if retries >= MAX_RETRIES:
                logger.error(f"서버 연결 실패 {MAX_RETRIES}회 연속 - 중단합니다.")
                break
            logger.warning(f"연결 실패 ({retries}/{MAX_RETRIES}) - 3초 후 재시도...")
            time.sleep(3)

        except requests.exceptions.HTTPError as e:
            errors += 1
            retries = 0
            logger.error(f"HTTP 에러: {e}")
            time.sleep(1)

        except Exception as e:
            errors += 1
            retries = 0
            logger.error(f"에러: {e}")
            time.sleep(1)

    return updated, deleted, errors


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LIMIT
    updated, deleted, errors = update_stale_summoners(limit)
    logger.info(f"완료 | 업데이트: {updated}건, 삭제: {deleted}건, 에러: {errors}건")

    if errors > 0:
        sys.exit(1)
