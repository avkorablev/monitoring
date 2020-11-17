import responses

from monitoring.checker import CheckResult, Rule, check


@responses.activate
def test_check():
    responses.add(responses.GET, 'http://test.com', status=200)
    rule = Rule('http://test.com')
    expected_result = CheckResult(10, 200, None)

    result = check(rule, 20)
    assert result.status_code == expected_result.status_code
    assert result.regexp_result == expected_result.regexp_result
    assert result.response_time is not None
    assert result.response_time > 0
