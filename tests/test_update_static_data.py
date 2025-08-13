import pytest
from update_static_data import get_latest_ddragon_version


def test_get_latest_ddragon_version():
    version = get_latest_ddragon_version()
    assert version is not None, "최신 DDragon 버전이 None이어서는 안 됩니다."
    assert isinstance(version, str), "버전은 문자열이어야 합니다."
    assert len(version) > 0, "버전 문자열이 비어있어서는 안 됩니다."

    parts = version.split(".")
    assert (
        len(parts) == 3
    ), "버전 형식이 잘못되었습니다. 예상 형식은 'major.minor.patch'입니다."
