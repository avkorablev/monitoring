from datetime import datetime
from unittest import mock

import pytest
import responses
from requests import ConnectTimeout

from monitoring.checker import CheckResult, Rule, check


test_check_data = [
    (
        dict(method=responses.GET, url='http://test.com', status=200),
        Rule('http://test.com', 1),
        CheckResult(datetime(2020, 11, 19), 'http://test.com', 10, 200, None)
    ),
    (
        dict(method=responses.GET, url='https://test.com', status=200),
        Rule('https://test.com', 1),
        CheckResult(datetime(2020, 11, 19), 'http://test.com', 10, 200, None)
    ),
    (
        dict(method=responses.HEAD, url='http://test.com', status=200),
        Rule('http://test.com', 1, 'HEAD'),
        CheckResult(datetime(2020, 11, 19), 'http://test.com', 10, 200, None)
    ),
    (
        dict(method=responses.GET, url='http://test.com', status=404),
        Rule('http://test.com', 1),
        CheckResult(datetime(2020, 11, 19), 'http://test.com', 10, 404, None)
    ),
    (
        dict(method=responses.GET, url='http://test.com', status=404),
        Rule('http://test.com', 1),
        CheckResult(datetime(2020, 11, 19), 'http://test.com', 10, 404, None)
    ),
    (
        dict(method=responses.GET, url='http://test.com', body=ConnectTimeout()),
        Rule('http://test.com', 1),
        CheckResult(datetime(2020, 11, 19), 'http://test.com', failed=True)
    ),
]


@responses.activate
@pytest.mark.parametrize("responses_add, rule, expected_result", test_check_data)
def test_check(responses_add, rule, expected_result):
    responses.add(**responses_add)

    with mock.patch('monitoring.checker.utcnow', return_value=datetime(2020, 11, 19)):
        result = check(rule, 20)
    assert result.failed == expected_result.failed
    assert result.status_code == expected_result.status_code
    assert result.regexp_result == expected_result.regexp_result
    if not result.failed:
        assert result.response_time is not None
        assert result.response_time > 0


def test_serializer():
    msg = CheckResult(datetime(2020, 11, 19), 'http://test.com', failed=True).serialize()
    expected_result = (b'{"utc_datetime": "2020-11-19T00:00:00", "rule_id": "http://test.com", "response_time": null, '
                       b'"status_code": null, "regexp_result": null, "failed": true}')
    print(msg)
    assert msg == expected_result


def test_deserializer():
    result = CheckResult.deserialize((b'{"utc_datetime": "2020-11-19T00:00:00", "rule_id": "http://test.com", '
                                      b'"response_time": null, "status_code": null, "regexp_result": null, '
                                      b'"failed": true}'))
    expected_result = CheckResult(datetime(2020, 11, 19), 'http://test.com', failed=True)
    assert result == expected_result
