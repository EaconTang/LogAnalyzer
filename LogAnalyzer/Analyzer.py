"""
Main class, generate a specific analyzer
Mediator Pattern
"""
from Inputs import Inputs
from Filters import Filters
from Outputs import Outputs


class BaseAnalyzer(object):
    """
    Main process flow:
        1. Inputs
        2. Filters
        3. Outputs
    """
    def deal_input(self):
        raise NotImplementedError

    def deal_filter(self):
        raise NotImplementedError

    def deal_output(self):
        raise NotImplementedError


class Analyzer(BaseAnalyzer):
    def __init__(self, _vars_dict):
        assert isinstance(vars_dict, dict)
        self._vars = _vars_dict

    def deal_input(self):
        res = Inputs().process()
        self._vars.update(res)

    def deal_filter(self):
        res = Filters(self._vars).process()
        self._vars.update(res)

    def deal_output(self):
        Outputs(self._vars).process()


if __name__ == '__main__':
    vars_dict = {}
    analyzer = Analyzer(vars_dict)
    analyzer.deal_input()
    analyzer.deal_filter()
    analyzer.deal_output()
