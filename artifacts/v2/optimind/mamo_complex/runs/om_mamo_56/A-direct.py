import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = 7
    num_stores = 4
    centers = list(range(1, num_centers + 1))
    stores = list(range(1, num_stores + 1))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers)
    model.stores = pyo.Set(initialize=stores)

    model.y = pyo.Var(model.centers, domain=pyo.Binary)
    model.x = pyo.Var(model.centers, model.stores, domain=pyo.NonNegativeReals)

    def cap_rule(md, k):
        return sum(md.x[k, j] for j in md.stores) <= capacity[k - 1] * md.y[k]

    def demand_rule(md, j):
        return sum(md.x[k, j] for k in md.centers) >= demand[j - 1]

    model.capacity_con = pyo.Constraint(model.centers, rule=cap_rule)
    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def obj_rule(md):
        return sum(opening_cost[k - 1] * md.y[k] for k in md.centers) + \
               sum(transport_cost[k - 1][j - 1] * md.x[k, j]
                   for k in md.centers for j in md.stores)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}