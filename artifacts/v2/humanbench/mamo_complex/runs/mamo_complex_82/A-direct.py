import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(9))
    arcs_raw = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (1, 0), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8),
        (3, 0), (3, 2), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6), (4, 7), (4, 8),
        (5, 2), (5, 3), (5, 4), (5, 6), (5, 7), (5, 8),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 7), (6, 8),
        (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 8),
        (8, 0), (8, 1), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
    ]
    arcs = [(i, j) for (i, j) in arcs_raw if params[f"capacity_{i}_{j}"] > 0]

    source = 0
    sink = 8

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def cap_rule(mdl, i, j):
        return params[f"capacity_{i}_{j}"]
    model.cap = pyo.Param(model.arcs, initialize=cap_rule, mutable=False)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def flow_bound(mdl, i, j):
        return mdl.flow[i, j] <= mdl.cap[i, j]
    model.flow_bound_con = pyo.Constraint(model.arcs, rule=flow_bound)

    def balance_rule(mdl, k):
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.balance_con = pyo.Constraint(nodes, rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in arcs if i == source) - \
               sum(mdl.flow[i, j] for (i, j) in arcs if j == source)
    model.obj_expr = pyo.Expression(rule=obj_rule)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}