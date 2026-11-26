import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_dc = 6
    num_store = 9

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.dc = pyo.RangeSet(0, num_dc - 1)
    model.store = pyo.RangeSet(0, num_store - 1)

    model.x = pyo.Var(model.dc, model.store, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.dc, domain=pyo.Binary)

    def obj_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in m.dc) + sum(
            transport_cost[i][j] * m.x[i, j]
            for i in m.dc
            for j in m.store
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.dc) >= demand[j]

    model.demand_con = pyo.Constraint(model.store, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.store) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.dc, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}