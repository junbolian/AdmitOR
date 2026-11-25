import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]
    nodes = [0, 1, 2, 3, 4, 5]

    supply = {k: params[f"supply_node{k}"] for k in nodes}
    capacity = {arc: params[f"capacity_{arc[0]}_{arc[1]}"] for arc in arcs}
    cost = {arc: params[f"cost_{arc[0]}_{arc[1]}"] for arc in arcs}

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity[(i, j)]

    model.cap_con = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(mdl, n):
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        return outflow - inflow == supply[n]

    model.balance = pyo.Constraint(pyo.Set(initialize=nodes), rule=balance_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.flow[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}