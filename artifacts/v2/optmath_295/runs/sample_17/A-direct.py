import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    usage_limit = params["pattern_usage_limit"]
    pattern_yield = params["pattern_yield"]

    n_patterns = len(usage_limit)
    n_widths = len(demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_patterns - 1)
    model.W = pyo.RangeSet(0, n_widths - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=lambda m, p: (0, usage_limit[p]))

    def obj_rule(m):
        return sum(m.x[p] for p in m.P)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, w):
        return sum(pattern_yield[p][w] * m.x[p] for p in m.P) >= demand[w]

    model.demand_con = pyo.Constraint(model.W, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}