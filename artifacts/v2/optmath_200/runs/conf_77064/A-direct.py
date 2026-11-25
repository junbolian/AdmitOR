import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_wh = len(supply)
    num_dc = len(demand)

    model = pyo.ConcreteModel()
    model.W = pyo.RangeSet(0, num_wh - 1)
    model.D = pyo.RangeSet(0, num_dc - 1)

    model.x = pyo.Var(model.W, model.D, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j]
                   for i in mdl.W for j in mdl.D)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.D) == supply[i]

    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.W) == demand[j]

    model.demand_con = pyo.Constraint(model.D, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.W, model.D, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}