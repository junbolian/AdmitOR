import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = 6
    n_stores = 8

    centers = list(range(n_centers))
    stores = list(range(n_stores))

    model = pyo.ConcreteModel()

    model.x_center = pyo.Set(initialize=centers)
    model.x_store = pyo.Set(initialize=stores)

    model.y = pyo.Var(model.x_center, domain=pyo.Binary)
    model.flow = pyo.Var(model.x_center, model.x_store, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in m.x_center) + sum(
            transport_cost[i][j] * m.flow[i, j]
            for i in m.x_center
            for j in m.x_store
        )

    model.profit_objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.x_center) == demand[j]

    model.demand_constraint = pyo.Constraint(model.x_store, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in m.x_store) <= capacity[i] * m.y[i]

    model.capacity_constraint = pyo.Constraint(model.x_center, rule=capacity_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.profit_objective))
    except Exception:
        return {"objective": None, "status": "no objective value"}

    return {"objective": obj_val, "status": "optimal"}