import os
import re
from typing import Dict, Set

import yaml

from monitoring.checker import Rule


def build_settings():
    with open(os.path.join(os.path.dirname(__file__), '..', 'setup.yaml'), 'r') as f:
        return yaml.safe_load(f)


def init_rules(yaml_path = os.path.join(os.path.dirname(__file__), '..', 'rules.yaml')) -> Set[Rule]:
    if not os.path.exists(yaml_path):
        raise ValueError('YAML file does not exist')
    with open(yaml_path, 'r') as f:
        rules = yaml.safe_load(f)
    return set((parse_rule(rule) for rule in rules or []))


def parse_rule(settings: Dict) -> Rule:
    for field in ['url', 'period']:
        if field not in settings:
            raise ValueError('There is an problem with parsing Rule: "{}" should be set'.format(field))
    return Rule(
        url=settings['url'],
        period=settings['period'],
        method=settings.get('method', None),
        regexp=None if 'regexp' not in settings else re.compile(settings['regexp'])
    )


def cert_files():
    ssl_cert_dir = os.path.join(os.path.dirname(__file__), '..', 'certs')
    ssl_cafile = os.path.join(ssl_cert_dir, 'ca.pem')
    ssl_certfile = os.path.join(ssl_cert_dir, 'service.cert')
    ssl_keyfile = os.path.join(ssl_cert_dir, 'service.key')
    return ssl_cafile, ssl_certfile, ssl_keyfile
