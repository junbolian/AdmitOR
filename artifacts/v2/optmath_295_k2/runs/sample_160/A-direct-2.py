import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost = params["shipping_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(fixed_cost)
    n_store = len(demand)

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, n_dc - 1)
    model.STORE = pyo.RangeSet(0, n_store - 1)

    model.x = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.DC, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(fixed_cost[i] * mdl.y[i] for i in mdl.DC) + sum(
            shipping_cost[i][j] * mdl.x[i, j]
            for i in mdl.DC
            for j in mdl.STORE
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.DC) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.STORE) <= capacity[i] * mdl.y[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}