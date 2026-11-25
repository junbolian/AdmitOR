import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    num_origins = len(supply)
    num_destinations = len(demand)

    model = pyo.ConcreteModel()

    model.ORIGINS = pyo.RangeSet(0, num_origins - 1)
    model.DESTINATIONS = pyo.RangeSet(0, num_destinations - 1)

    model.x = pyo.Var(model.ORIGINS, model.DESTINATIONS, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.DESTINATIONS) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.ORIGINS) == demand[j]

    model.supply_constraint = pyo.Constraint(model.ORIGINS, rule=supply_rule)
    model.demand_constraint = pyo.Constraint(model.DESTINATIONS, rule=demand_rule)

    def objective_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j]
                   for i in mdl.ORIGINS for j in mdl.DESTINATIONS)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or unbounded"}

    return {"objective": obj_val, "status": "optimal"}