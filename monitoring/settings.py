import os
import re
from typing import Dict, Set

import yaml

from monitoring.checker import Rule


def build_settings():
    with open(os.path.join(os.path.dirname(__file__), '..', 'setup.yaml'), 'r') as f:
        return yaml.safe_load(f)


def init_rules(yaml_path: str) -> Set[Rule]:
    if not os.path.exists(yaml_path):
        raise ValueError('YAML file does not exist')
    with open(yaml_path, 'r') as f:
        rules = yaml.safe_load(f)
    return set((parse_rule(rule) for rule in rules or []))


def parse_rule(settings: Dict) -> Rule:
    if 'url' not in settings:
        raise ValueError('There is an problem with parsing Rule')
    return Rule(
        url=settings['url'],
        method=settings.get('method', None),
        regexp=None if 'regexp' not in settings else re.compile(settings['regexp'])
    )
