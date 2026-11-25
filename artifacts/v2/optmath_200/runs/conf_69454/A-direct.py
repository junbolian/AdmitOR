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

    model.x = pyo.Var(model.origins, model.dests, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.origins for j in mdl.dests)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.dests) == supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.origins) == demand[j]

    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception as e:
        return {"objective": None, "status": "infeasible or solver failure"}

    return {"objective": obj_val, "status": "optimal"}