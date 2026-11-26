import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = 7
    nodes = list(range(n))

    # transport_costs is row-major for i != j pairs only (directed, all ordered pairs)
    cost = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            cost[(i, j)] = transport_costs[idx]
            idx += 1

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j],
        dimen=2,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        rule=lambda m: sum(cost[(i, j)] * m.flow[i, j] for (i, j) in m.arcs),
        sense=pyo.minimize,
    )

    def balance_rule(m, k):
        inflow = sum(m.flow[i, k] for i in nodes if i != k)
        outflow = sum(m.flow[k, j] for j in nodes if j != k)
        return supplies[k] + inflow - outflow == demands[k]

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}