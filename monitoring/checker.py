from dataclasses import dataclass
from typing import Optional, Pattern

import requests


@dataclass
class Rule:
    url: str
    method: str = 'GET'
    regexp: Optional[Pattern[str]] = None


@dataclass
class CheckResult:
    response_time: float
    status_code: int
    regexp_result: Optional[bool]


def check(rule: Rule, timeout: float) -> CheckResult:
    response = requests.request(method=rule.method, url=rule.url, timeout=timeout)

    result = CheckResult(
        response_time=response.elapsed.total_seconds(),  # Response time https://stackoverflow.com/a/43260678
        status_code=response.status_code,
        regexp_result=None,
    )

    if rule.regexp:
        result.regexp_result = bool(rule.regexp.match(response.text))

    return result
