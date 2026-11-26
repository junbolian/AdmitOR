import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dc = len(opening_cost)
    num_store = len(demand)

    dc_idx = list(range(num_dc))
    store_idx = list(range(num_store))

    model = pyo.ConcreteModel()

    model.DC = pyo.Set(initialize=dc_idx)
    model.STORE = pyo.Set(initialize=store_idx)

    model.y = pyo.Var(model.DC, domain=pyo.Binary)
    model.x = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in m.DC) + sum(
            transport_cost[i][j] * m.x[i, j] for i in m.DC for j in m.STORE
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.DC) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.STORE) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}