import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    num_origins = params["num_origins"]
    num_destinations = params["num_destinations"]

    model = pyo.ConcreteModel()

    model.ORIGINS = pyo.RangeSet(0, num_origins - 1)
    model.DESTS = pyo.RangeSet(0, num_destinations - 1)

    model.x = pyo.Var(model.ORIGINS, model.DESTS, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.ORIGINS for j in m.DESTS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.DESTS) <= supply[i]
    model.supply_con = pyo.Constraint(model.ORIGINS, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.ORIGINS) == demand[j]
    model.demand_con = pyo.Constraint(model.DESTS, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}