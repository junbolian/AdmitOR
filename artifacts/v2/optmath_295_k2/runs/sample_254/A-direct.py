import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.destinations = pyo.RangeSet(0, n_destinations - 1)

    model.x = pyo.Var(model.origins, model.destinations, within=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.destinations) <= supply[i]
    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) >= demand[j]
    model.demand_con = pyo.Constraint(model.destinations, rule=demand_rule)

    def limit_rule(m, i, j):
        return m.x[i, j] <= limit[i][j]
    model.limit_con = pyo.Constraint(model.origins, model.destinations, rule=limit_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.origins for j in m.destinations)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}