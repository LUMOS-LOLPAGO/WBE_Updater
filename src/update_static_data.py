import requests
import json
from common import configure_logger, load_env, ServerRequestError

logger = configure_logger()

# 환경 변수 불러오기
env = load_env(["SERVER_URL"])
SERVER_URL = env.get("SERVER_URL")


# 정적 데이터 업데이트 요청을 보내는 함수
def update_static_data(ddragon_version: str) -> None:
    url = f"{SERVER_URL}/static-data/update-all"
    params = {
        "dDragonVersion": ddragon_version,
        "region": "KR",
    }

    res = requests.put(url, params=params)
    if res.status_code != 200:
        raise ServerRequestError(
            f"정적 데이터 업데이트 요청 실패: {res.status_code} - {res.text}"
        )


# 최신 dDragon 버전 정보를 가져오는 함수
def get_latest_ddragon_version() -> str:
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url)
    if response.status_code != 200:
        raise ServerRequestError(
            f"ddragon 버전 정보 요청 실패: {response.status_code} - {response.text}"
        )
    versions = response.json()
    return versions[0] if versions else None


if __name__ == "__main__":
    ddragon_version = get_latest_ddragon_version()
    update_static_data(ddragon_version)
    logger.info(f"정적 데이터 업데이트 완료 (버전: {ddragon_version})")
