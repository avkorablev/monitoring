from typing import Set

from monitoring import rules_registry
from monitoring.checker import Rule, check

TIMEOUT = 10


def init_rules() -> Set[Rule]:
    return rules_registry.rules


def main():
    rules = init_rules()
    results = [check(rule, TIMEOUT) for rule in rules]
    print(results)


if __name__ == '__main__':
    main()
