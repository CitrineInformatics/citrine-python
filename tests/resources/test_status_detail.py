import pytest

from citrine.resources.status_detail import StatusDetail, StatusLevelEnum


@pytest.fixture
def info():
    return StatusDetail(msg="an info message", level=StatusLevelEnum.INFO)


@pytest.fixture
def warning():
    return StatusDetail(msg="a warning message", level=StatusLevelEnum.WARNING)


@pytest.fixture
def error():
    return StatusDetail(msg="an error message", level=StatusLevelEnum.ERROR)


@pytest.fixture
def unknown():
    return StatusDetail(msg="an unknown message", level=StatusLevelEnum.UNKNOWN)


def test_str(info, warning, error, unknown):
    assert StatusLevelEnum.INFO.lower() in str(info).lower()
    assert info.msg in str(info)
    assert StatusLevelEnum.WARNING.lower() in str(warning).lower()
    assert warning.msg in str(warning)
    assert StatusLevelEnum.ERROR.lower() in str(error).lower()
    assert error.msg in str(error)
    assert StatusLevelEnum.UNKNOWN.lower() in str(unknown).lower()
    assert unknown.msg in str(unknown)


def test_repr(info, warning, error, unknown):
    assert StatusLevelEnum.INFO.lower() in repr(info).lower()
    assert info.msg in repr(info)
    assert StatusLevelEnum.WARNING.lower() in repr(warning).lower()
    assert warning.msg in repr(warning)
    assert StatusLevelEnum.ERROR.lower() in repr(error).lower()
    assert error.msg in repr(error)
    assert StatusLevelEnum.UNKNOWN.lower() in repr(unknown).lower()
    assert unknown.msg in repr(unknown)
