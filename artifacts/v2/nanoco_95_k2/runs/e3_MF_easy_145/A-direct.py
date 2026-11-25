import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(9))
    source = 0
    sink = 8

    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]

    cap = {}
    cost = {}
    for (i, j) in arcs:
        cap[(i, j)] = params["capacity_%d_%d" % (i, j)]
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def _cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=_cap_rule)

    def _bal_rule(mdl, k):
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == k)
        return inflow == outflow
    model.balance_con = pyo.Constraint([1, 2, 3, 4, 5, 6, 7], rule=_bal_rule)

    def _obj_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in arcs if i == source)
    model.total_outflow = pyo.Objective(rule=_obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_outflow))
    return {"objective": obj_val, "status": "optimal"}