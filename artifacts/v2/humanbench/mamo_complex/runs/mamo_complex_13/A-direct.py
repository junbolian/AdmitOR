import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = list(range(len(opening_cost)))
    stores = list(range(len(demand)))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)
    model.CS = pyo.Set(initialize=[(c, s) for c in centers for s in stores])

    model.x = pyo.Var(model.CS, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.C, within=pyo.Binary)

    def obj_rule(m):
        return sum(opening_cost[c] * m.y[c] for c in m.C) + sum(
            transport_cost[c][s] * m.x[c, s] for (c, s) in m.CS
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, s):
        return sum(m.x[c, s] for c in m.C) == demand[s]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def cap_rule(m, c):
        return sum(m.x[c, s] for s in m.S) <= capacity[c] * m.y[c]

    model.cap_con = pyo.Constraint(model.C, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}