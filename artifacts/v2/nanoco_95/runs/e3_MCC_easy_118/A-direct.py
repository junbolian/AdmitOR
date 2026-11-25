import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = [0, 1, 2, 3, 4, 5]
    arcs = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    ]

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    def flow_bounds(mdl, i, j):
        lb = params.get("min_flow_%d_%d" % (i, j), 0.0)
        ub = params["cap_%d_%d" % (i, j)]
        return (lb, ub)

    model.flow = pyo.Var(model.ARCS, bounds=flow_bounds)

    def flow_balance_rule(mdl, k):
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == k)
        return inflow == outflow

    model.flow_balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    def total_cost_rule(mdl):
        return sum(params["cost_%d_%d" % (i, j)] * mdl.flow[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}