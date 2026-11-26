import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(6))
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    ]

    def cap_key(i, j):
        return "capacity_%d_%d" % (i, j)

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=nodes)
    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return params[cap_key(i, j)]

    model.capacity = pyo.Param(model.arc_set, initialize=cap_rule,
                               within=pyo.NonNegativeReals)

    def flow_ub_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity[i, j]

    model.flow_ub = pyo.Constraint(model.arc_set, rule=flow_ub_rule)

    model.flow_value = pyo.Var(domain=pyo.NonNegativeReals)

    def net_out_rule(mdl, k):
        out_term = sum(mdl.flow[k, j] for (i, j) in arcs if i == k)
        in_term = sum(mdl.flow[i, k] for (i, j) in arcs if j == k)
        if k == 0:
            return mdl.flow_value == out_term - in_term
        if k == 5:
            return out_term - in_term == -mdl.flow_value
        return out_term - in_term == 0

    model.balance = pyo.Constraint(model.node_set, rule=net_out_rule)

    model.obj = pyo.Objective(expr=model.flow_value, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}