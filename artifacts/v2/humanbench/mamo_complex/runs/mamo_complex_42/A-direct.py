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

    model.centers = pyo.RangeSet(0, n_centers - 1)
    model.stores = pyo.RangeSet(0, n_stores - 1)

    model.y = pyo.Var(model.centers, within=pyo.Binary)
    model.x = pyo.Var(model.centers, model.stores, within=pyo.NonNegativeReals)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.centers) >= demand[j]
    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.stores) <= capacity[i] * mdl.y[i]
    model.cap_con = pyo.Constraint(model.centers, rule=cap_rule)

    def obj_rule(mdl):
        return sum(opening_cost[i] * mdl.y[i] for i in mdl.centers) + \
               sum(transport_cost[i][j] * mdl.x[i, j]
                   for i in mdl.centers for j in mdl.stores)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}