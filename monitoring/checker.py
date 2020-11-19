from dataclasses import dataclass
from typing import Optional, Pattern

import requests


@dataclass
class Rule:
    url: str
    period: int
    method: str = 'GET'
    regexp: Optional[Pattern[str]] = None

    def __hash__(self):
        return hash("{}:{}:{}".format(self.url, self.method, self.regexp))


@dataclass
class CheckResult:
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    regexp_result: Optional[bool] = None
    failed: bool = False  # can be True only if ConnectionError has happened


def check(rule: Rule, timeout: float) -> CheckResult:
    try:
        response = requests.request(method=rule.method, url=rule.url, timeout=timeout)
    except requests.ConnectionError:
        return CheckResult(failed=True)

    result = CheckResult(
        response_time=response.elapsed.total_seconds(),  # Response time https://stackoverflow.com/a/43260678
        status_code=response.status_code,
        regexp_result=None,
    )

    if rule.regexp:
        result.regexp_result = bool(rule.regexp.match(response.text))

    return result
