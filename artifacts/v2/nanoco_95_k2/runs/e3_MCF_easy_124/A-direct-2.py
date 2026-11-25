import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5]
    arcs = [(0, 2), (0, 3), (1, 2), (1, 3), (2, 4), (2, 5),
            (3, 4), (3, 5), (0, 4), (0, 5), (1, 4), (1, 5)]

    supply = params["supply"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.supply = pyo.Param(model.NODES, initialize={n: supply[n] for n in nodes})
    model.cap = pyo.Param(model.ARCS, initialize={a: capacity[i] for i, a in enumerate(arcs)})
    model.unit_cost = pyo.Param(model.ARCS, initialize={a: cost[i] for i, a in enumerate(arcs)})

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.cap[i, j]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def bal_rule(mdl, n):
        out_flow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        in_flow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        return out_flow - in_flow == mdl.supply[n]
    model.balance_con = pyo.Constraint(model.NODES, rule=bal_rule)

    def obj_rule(mdl):
        return sum(mdl.unit_cost[i, j] * mdl.flow[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}