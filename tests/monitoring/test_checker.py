import pytest
import responses
from requests import ConnectTimeout

from monitoring.checker import CheckResult, Rule, check


test_check_data = [
    (
        dict(method=responses.GET, url='http://test.com', status=200),
        Rule('http://test.com', 1),
        CheckResult(10, 200, None)
    ),
    (
        dict(method=responses.GET, url='https://test.com', status=200),
        Rule('https://test.com', 1),
        CheckResult(10, 200, None)
    ),
    (
        dict(method=responses.HEAD, url='http://test.com', status=200),
        Rule('http://test.com', 1, 'HEAD'),
        CheckResult(10, 200, None)
    ),
    (
        dict(method=responses.GET, url='http://test.com', status=404),
        Rule('http://test.com', 1),
        CheckResult(10, 404, None)
    ),
    (
        dict(method=responses.GET, url='http://test.com', status=404),
        Rule('http://test.com', 1),
        CheckResult(10, 404, None)
    ),
    (
        dict(method=responses.GET, url='http://test.com', body=ConnectTimeout()),
        Rule('http://test.com', 1),
        CheckResult(failed=True)
    ),
]


@responses.activate
@pytest.mark.parametrize("responses_add, rule, expected_result", test_check_data)
def test_check(responses_add, rule, expected_result):
    responses.add(**responses_add)

    result = check(rule, 20)
    assert result.failed == expected_result.failed
    assert result.status_code == expected_result.status_code
    assert result.regexp_result == expected_result.regexp_result
    if not result.failed:
        assert result.response_time is not None
        assert result.response_time > 0
