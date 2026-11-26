import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)

    centers = range(n_centers)
    stores = range(n_stores)

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=list(centers))
    model.S = pyo.Set(initialize=list(stores))

    model.y = pyo.Var(model.C, within=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(opening_cost[i] * mdl.y[i] for i in mdl.C) + sum(
            transport_cost[i][j] * mdl.x[i, j] for i in mdl.C for j in mdl.S
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.C) >= demand[j]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.S) <= capacity[i] * mdl.y[i]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}