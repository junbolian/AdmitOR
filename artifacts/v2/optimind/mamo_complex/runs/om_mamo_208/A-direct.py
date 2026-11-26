import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (1, 2, "capacity_1_2"),
        (1, 3, "capacity_1_3"),
        (2, 3, "capacity_2_3"),
        (2, 4, "capacity_2_4"),
        (3, 4, "capacity_3_4"),
    ]
    nodes = [1, 2, 3, 4]
    source = 1
    sink = 4

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=[(u, v) for (u, v, _) in edges], dimen=2)

    flow_init = {(u, v): 0.0 for (u, v, _) in edges}
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals, initialize=flow_init)

    cap_data = {(u, v): float(params[pname]) for (u, v, pname) in edges}

    def cap_rule(mdl, u, v):
        return mdl.flow[u, v] <= cap_data[(u, v)]

    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    def balance_rule(mdl, n):
        inflow = sum(mdl.flow[u, v] for (u, v) in mdl.arcs if v == n)
        outflow = sum(mdl.flow[u, v] for (u, v) in mdl.arcs if u == n)
        if n == source:
            return outflow - inflow >= 0
        elif n == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(pyo.Set(initialize=nodes), rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[u, v] for (u, v) in mdl.arcs if u == source) - \
               sum(mdl.flow[u, v] for (u, v) in mdl.arcs if v == source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}