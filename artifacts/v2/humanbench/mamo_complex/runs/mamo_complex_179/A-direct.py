import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    store_demand = params["store_demand"]
    dc_capacity = params["dc_capacity"]

    num_dc = len(opening_cost)
    num_store = len(store_demand)

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, num_dc - 1)
    model.STORE = pyo.RangeSet(0, num_store - 1)

    model.open = pyo.Var(model.DC, domain=pyo.Binary)
    model.ship = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return (
            sum(opening_cost[i] * mdl.open[i] for i in mdl.DC)
            + sum(transport_cost[i][j] * mdl.ship[i, j] for i in mdl.DC for j in mdl.STORE)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.ship[i, j] for i in mdl.DC) >= store_demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(mdl, i):
        return sum(mdl.ship[i, j] for j in mdl.STORE) <= dc_capacity[i] * mdl.open[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}