import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_dc = 7
    num_store = 8

    fixed_cost_dc = params["fixed_cost_dc"]
    shipping_cost = params["shipping_cost"]
    store_demand = params["store_demand"]
    dc_capacity = params["dc_capacity"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, num_dc - 1)
    model.STORE = pyo.RangeSet(0, num_store - 1)

    model.open_dc = pyo.Var(model.DC, domain=pyo.Binary)
    model.ship = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost_dc[i] * m.open_dc[i] for i in m.DC) + \
               sum(shipping_cost[i][j] * m.ship[i, j] for i in m.DC for j in m.STORE)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.DC) == store_demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.ship[i, j] for j in m.STORE) <= dc_capacity[i] * m.open_dc[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}