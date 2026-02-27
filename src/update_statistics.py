import sys
import json
import requests
from common import configure_logger, load_env

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["SERVER_URL"])
SERVER_URL = env.get("SERVER_URL")

SUMMONER_MATCHES_FILE_PATH = "summoner_matches.json"
BATCH_SIZE = 100


def update_statistics(match_ids: list[str]) -> dict:
    url = f"{SERVER_URL}/statistics/update"

    total_result = {
        "queued": 0,
        "alreadyProcessed": 0,
        "failed": 0,
    }

    # 서버 과부하를 막기 위해 chunk 단위로 나누어 요청
    for i in range(0, len(match_ids), BATCH_SIZE):
        chunk = match_ids[i : i + BATCH_SIZE]
        logger.info(
            f"[{i + 1}/{min(i + BATCH_SIZE, len(match_ids))}] 번째 매치 그룹 전송 중 (총 {len(match_ids)}개)..."
        )

        try:
            res = requests.post(url, json={"matchIds": chunk})

            if res.status_code == 200:
                result = res.json()
                total_result["queued"] += result.get("queued", 0)
                total_result["alreadyProcessed"] += result.get("alreadyProcessed", 0)
            else:
                logger.error(f"요청 실패: {res.status_code} - {res.text}")
                total_result["failed"] += len(chunk)

        except Exception as e:
            logger.error(f"요청 중 에러 발생: {e}")
            total_result["failed"] += len(chunk)

    return total_result


if __name__ == "__main__":
    try:
        with open(SUMMONER_MATCHES_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {SUMMONER_MATCHES_FILE_PATH}")
        sys.exit(1)

    # 딕셔너리의 value들(리스트들)에서 고유 매치 ID 추출
    unique_match_ids = set()
    for matches in data.values():
        unique_match_ids.update(matches)

    match_ids = list(unique_match_ids)

    if not match_ids:
        logger.info("업데이트할 매치가 없습니다.")
        sys.exit(0)

    logger.info(f"총 {len(match_ids)}개의 고유 매치에 대해 통계 업데이트를 시작합니다.")

    result = update_statistics(match_ids)

    logger.info("\n=== 통계 업데이트 처리 결과 요약 ===")
    logger.info(f"MQ로 전송된 매치 수: {result['queued']}")
    logger.info(f"이미 처리된 매치 수: {result['alreadyProcessed']}")
    logger.info(f"API 요청 실패 수: {result['failed']}")
    logger.info("=====================================")

    if result["failed"] > 0:
        logger.error("API 요청 실패가 존재하여 비정상 종료합니다.")
        sys.exit(1)
    else:
        logger.info("모든 매치 전송 요청이 완료되었습니다.")
