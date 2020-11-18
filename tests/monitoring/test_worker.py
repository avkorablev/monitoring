import os
import re

import pytest

from monitoring import Rule, rules_registry
from monitoring.worker import init_rules, parse_rule


def test_registry():
    assert rules_registry.rules == set()
    rule = Rule('http://test.com')
    rules_registry.register(rule)
    assert rules_registry.rules == {rule}


def test_init_rules_yaml_not_exist():
    with pytest.raises(ValueError):
        init_rules('')


def test_init_rules():
    rules = init_rules(os.path.join(os.path.dirname(__file__), '..', 'rules', 'empty.yaml'))
    assert rules == set()


def test_init_rules_file_with_rule():
    rules = init_rules(os.path.join(os.path.dirname(__file__), '..', 'rules', 'one_rule.yaml'))
    assert rules == {Rule('http://test.com', 'POST', re.compile('.*'))}


def test_parse_rule():
    input_dict = {
        'url': 'http://test.com',
        'method': 'POST',
        'regexp': '.*'
    }

    expected_rule = Rule('http://test.com', 'POST', re.compile('.*'))

    assert parse_rule(input_dict) == expected_rule
