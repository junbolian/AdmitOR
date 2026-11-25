import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n_origins = len(supply)
    n_dests = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.dests = pyo.RangeSet(0, n_dests - 1)

    model.x = pyo.Var(model.origins, model.dests, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.origins for j in m.dests)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.dests) == supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) == demand[j]

    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}