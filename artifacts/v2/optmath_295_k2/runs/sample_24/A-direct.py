import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(supply)
    m = len(demand)
    origins = list(range(n))
    destinations = list(range(m))

    model = pyo.ConcreteModel()

    model.ORIGINS = pyo.Set(initialize=origins)
    model.DESTINATIONS = pyo.Set(initialize=destinations)

    model.x = pyo.Var(model.ORIGINS, model.DESTINATIONS, within=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.DESTINATIONS) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.ORIGINS) == demand[j]

    def capacity_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.supply_cons = pyo.Constraint(model.ORIGINS, rule=supply_rule)
    model.demand_cons = pyo.Constraint(model.DESTINATIONS, rule=demand_rule)
    model.capacity_cons = pyo.Constraint(model.ORIGINS, model.DESTINATIONS, rule=capacity_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.ORIGINS for j in mdl.DESTINATIONS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}