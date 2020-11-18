from monitoring.checker import Rule


class Registry:
    def __init__(self):
        self._rules = set()

    def register(self, rule: Rule):
        self._rules.add(rule)

    @property
    def rules(self):
        return self._rules


rules_registry = Registry()
