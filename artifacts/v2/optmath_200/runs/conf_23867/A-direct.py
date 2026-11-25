import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4, 5, 6]
    n = len(nodes)
    net_supply = params["net_supply"]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.NODE = pyo.Set(initialize=nodes)

    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}
    cap = {(i, j): params["cap_%d_%d" % (i, j)] for (i, j) in arcs}

    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals,
                         bounds=lambda m, i, j: (0.0, cap[(i, j)]))

    def balance_rule(m, k):
        out_flow = sum(m.flow[k, j] for j in nodes if j != k)
        in_flow = sum(m.flow[i, k] for i in nodes if i != k)
        return out_flow - in_flow == net_supply[k]

    model.balance = pyo.Constraint(model.NODE, rule=balance_rule)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.flow[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}