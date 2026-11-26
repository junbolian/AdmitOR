import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hospitals = [1, 2, 3, 4]
    supply = {i: params[f"supply"] if False else params["supply"][i - 1] for i in hospitals}
    demand = {i: params["demand"][i - 1] for i in hospitals}

    cost = {}
    for i in hospitals:
        for j in hospitals:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()

    model.hospitals = pyo.Set(initialize=hospitals)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in hospitals for j in hospitals if i != j],
        dimen=2,
    )

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.flow[i, j] for (i, j) in m.arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, h):
        outgoing = sum(m.flow[h, j] for j in hospitals if j != h)
        incoming = sum(m.flow[i, h] for i in hospitals if i != h)
        return supply[h] - outgoing + incoming >= demand[h]
    model.balance = pyo.Constraint(model.hospitals, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}