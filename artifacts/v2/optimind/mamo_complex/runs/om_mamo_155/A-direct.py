import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = list(range(1, 6))
    stores = list(range(1, 10))

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)
    model.CS = pyo.Set(initialize=[(c, s) for c in centers for s in stores])

    model.y = pyo.Var(model.C, domain=pyo.Binary)
    model.x = pyo.Var(model.CS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_cost[c - 1] * m.y[c] for c in m.C) + \
               sum(transport_cost[c - 1][s - 1] * m.x[c, s] for (c, s) in m.CS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, s):
        return sum(m.x[c, s] for c in m.C) == demand[s - 1]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(m, c):
        return sum(m.x[c, s] for s in m.S) <= capacity[c - 1] * m.y[c]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}