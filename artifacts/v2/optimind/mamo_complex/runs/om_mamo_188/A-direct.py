import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(opening_cost)
    n_store = len(demand)

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, n_dc - 1)
    model.STORE = pyo.RangeSet(0, n_store - 1)

    model.y = pyo.Var(model.DC, within=pyo.Binary)
    model.x = pyo.Var(model.DC, model.STORE, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return (
            sum(opening_cost[i] * mdl.y[i] for i in mdl.DC)
            + sum(transport_cost[i][j] * mdl.x[i, j] for i in mdl.DC for j in mdl.STORE)
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.DC) >= demand[j]

    model.demand_rule = pyo.Constraint(model.STORE, rule=demand_rule)

    def cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.STORE) <= capacity[i] * mdl.y[i]

    model.cap_rule = pyo.Constraint(model.DC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}