import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    centers = list(range(8))
    stores = list(range(9))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def transport_rule(mdl, i, j):
        return mdl.x[i, j] <= demand[j] * mdl.y[i]

    model.link = pyo.Constraint(centers, stores, rule=transport_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in centers) == demand[j]

    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in stores) <= capacity[i] * mdl.y[i]

    model.capacity_con = pyo.Constraint(centers, rule=capacity_rule)

    def obj_rule(mdl):
        return sum(opening_cost[i] * mdl.y[i] for i in centers) + sum(
            transport_cost[i][j] * mdl.x[i, j] for i in centers for j in stores
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}