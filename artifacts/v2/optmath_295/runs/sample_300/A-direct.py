import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    shipping_capacity = params["shipping_capacity"]

    n_wh = len(supply)
    n_store = len(demand)
    n_prod = len(supply[0])

    model = pyo.ConcreteModel()

    model.wh = pyo.RangeSet(0, n_wh - 1)
    model.st = pyo.RangeSet(0, n_store - 1)
    model.pr = pyo.RangeSet(0, n_prod - 1)

    model.x = pyo.Var(model.wh, model.st, model.pr, domain=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(
            transport_cost[i][j][p] * md.x[i, j, p]
            for i in md.wh
            for j in md.st
            for p in md.pr
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(md, i, p):
        return sum(md.x[i, j, p] for j in md.st) <= supply[i][p]

    model.supply_con = pyo.Constraint(model.wh, model.pr, rule=supply_rule)

    def demand_rule(md, j, p):
        return sum(md.x[i, j, p] for i in md.wh) >= demand[j][p]

    model.demand_con = pyo.Constraint(model.st, model.pr, rule=demand_rule)

    def cap_rule(md, i, j):
        return sum(md.x[i, j, p] for p in md.pr) <= shipping_capacity[i][j]

    model.cap_con = pyo.Constraint(model.wh, model.st, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}