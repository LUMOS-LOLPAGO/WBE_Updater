# .github/scripts/common.py
import os
import logging
from dotenv import load_dotenv


# 로깅 설정
def configure_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


# 환경변수 로드 및 검증
def load_env(required_keys: list[str]) -> dict:
    load_dotenv(dotenv_path=".env")
    env = {key: os.getenv(key) for key in required_keys}
    missing = [k for k, v in env.items() if v is None]
    if missing:
        raise ValueError(f"환경 변수 읽기 실패: {', '.join(missing)}")
    return env


class ServerRequestError(Exception):
    pass
