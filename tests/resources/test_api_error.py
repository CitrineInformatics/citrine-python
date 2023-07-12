import pytest

from citrine.resources.api_error import ApiError, ValidationError


def test_has_failure():
    error = ApiError.build({
        "code": 400,
        "message": "you messed up",
        "validation_errors": [
            {"failure_message": 'failure 1', "failure_id": 'fail.one'},
            {"failure_message": 'failure 2', "failure_id": 'fail.two'},
            {"failure_message": 'vague failure'},
        ]
    })
    assert error.has_failure('fail.one')
    assert error.has_failure('fail.two')
    assert not error.has_failure('not.present')

    with pytest.raises(ValueError):
        error.has_failure(None)
    with pytest.raises(ValueError):
        error.has_failure('')


def test_deserialization():
    msg = 'ya failed'
    missing_id = {
        'code': 400,
        'message': 'an error',
        'validation_errors': [
            {
                'failure_message': msg,
            }
        ]
    }
    error = ApiError.build(missing_id)
    assert error.validation_errors[0].failure_message == msg

    with_id = {
        'code': 400,
        'message': 'an error',
        'validation_errors': [
            {
                'failure_message': msg,
                'failure_id': 'foo.id'
            }
        ]
    }
    error_with_id = ApiError.build(with_id)
    assert error_with_id.validation_errors[0].failure_id == 'foo.id'
