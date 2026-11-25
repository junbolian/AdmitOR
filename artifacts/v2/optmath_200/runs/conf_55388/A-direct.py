import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 7
    nodes = list(range(N))

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    supply = {i: 0.0 for i in nodes}
    supply[0] = params["supply_node_0"]
    supply[6] = -params["demand_node_6"]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.balance = pyo.Constraint(
        model.nodes,
        rule=lambda model, k: sum(model.x[k, j] for j in nodes if (k, j) in model.arcs)
        - sum(model.x[i, k] for i in nodes if (i, k) in model.arcs)
        == supply[k]
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}