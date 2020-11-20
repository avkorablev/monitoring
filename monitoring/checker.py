import json
from dataclasses import dataclass
from datetime import datetime
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
    utc_time: datetime
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    regexp_result: Optional[bool] = None
    failed: bool = False  # can be True only if ConnectionError has happened

    @classmethod
    def deserialize(cls, message: bytes) -> 'CheckResult':
        msg_dict = json.loads(message.decode('utf-8'))
        return cls(
            utc_time=datetime.fromisoformat(msg_dict['utc_datetime']),
            response_time=msg_dict['response_time'],
            status_code=msg_dict['status_code'],
            regexp_result=msg_dict['regexp_result'],
            failed=msg_dict['failed']
        )

    def serialize(self) -> bytes:
        return json.dumps({
            'utc_datetime': self.utc_time.isoformat(),
            'response_time': self.response_time,
            'status_code': self.status_code,
            'regexp_result': self.regexp_result,
            'failed': self.failed
        }).encode('utf-8')


def utcnow():
    return datetime.utcnow()


def check(rule: Rule, timeout: float) -> CheckResult:
    try:
        response = requests.request(method=rule.method, url=rule.url, timeout=timeout)
    except requests.ConnectionError:
        return CheckResult(utc_time=utcnow(), failed=True)

    result = CheckResult(
        utc_time=utcnow(),
        response_time=response.elapsed.total_seconds(),  # Response time https://stackoverflow.com/a/43260678
        status_code=response.status_code,
        regexp_result=None,
    )

    if rule.regexp:
        result.regexp_result = bool(rule.regexp.match(response.text))

    return result
