import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    capacities = params["capacities"]
    costs = params["costs"]

    arcs = [
        (0, 2), (0, 3), (1, 2), (1, 3),
        (2, 4), (2, 5), (3, 4), (3, 5),
        (0, 4), (0, 5), (1, 4), (1, 5),
    ]
    nodes = list(range(6))

    cap_map = {arcs[i]: capacities[i] for i in range(len(arcs))}
    cost_map = {arcs[i]: costs[i] for i in range(len(arcs))}
    supply_map = {nodes[i]: supplies[i] for i in range(len(nodes))}

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.f = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.f[i, j] <= cap_map[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def balance_rule(m, k):
        outflow = sum(m.f[i, j] for (i, j) in arcs if i == k)
        inflow = sum(m.f[i, j] for (i, j) in arcs if j == k)
        return outflow - inflow == supply_map[k]
    model.balance_con = pyo.Constraint(model.NODES, rule=balance_rule)

    def obj_rule(m):
        return sum(cost_map[(i, j)] * m.f[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}