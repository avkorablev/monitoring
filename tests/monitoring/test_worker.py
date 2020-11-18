from monitoring import Rule, rules_registry
from monitoring.worker import init_rules


def test_registry():
    assert rules_registry.rules == set()
    rule = Rule('http://test.com')
    rules_registry.register(rule)
    assert rules_registry.rules == {rule}


def test_init_rules():
    rules = init_rules()
    assert rules == set()
