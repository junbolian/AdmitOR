import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, n_centers - 1)
    model.S = pyo.RangeSet(0, n_stores - 1)

    model.y = pyo.Var(model.C, domain=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in m.C) + sum(
            transport_cost[i][j] * m.x[i, j] for i in m.C for j in m.S
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.C) == demand[j]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.S) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}