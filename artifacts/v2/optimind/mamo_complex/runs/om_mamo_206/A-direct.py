import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)
    centers = list(range(num_centers))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def trans_rule(mdl, i, j):
        return mdl.x[i, j]

    def open_rule(mdl, i):
        return mdl.y[i]

    model.trans_cost = pyo.Expression(centers, stores, rule=trans_rule)
    model.open_cost = pyo.Expression(centers, rule=open_rule)

    def obj_rule(mdl):
        return (
            sum(opening_cost[i] * mdl.y[i] for i in centers)
            + sum(transport_cost[i][j] * mdl.x[i, j] for i in centers for j in stores)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in centers) == demand[j]

    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in stores) <= capacity[i] * mdl.y[i]

    model.cap_con = pyo.Constraint(centers, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}