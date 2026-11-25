import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---- Structural data (arc list is structural, not numeric params) ----
    nodes = [0, 1, 2, 3, 4, 5]
    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]

    supply = {n: params["supply_node" + str(n)] for n in nodes}
    cap = {a: params["capacity_{}_{}".format(a[0], a[1])] for a in arcs}
    cost = {a: params["cost_{}_{}".format(a[0], a[1])] for a in arcs}

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=nodes)
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def flow_ub(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=flow_ub)

    def balance_rule(mdl, n):
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        return outflow - inflow == supply[n]
    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.flow[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}