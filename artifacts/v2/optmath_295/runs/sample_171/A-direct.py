import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)
    origins = range(n_origins)
    destinations = range(n_destinations)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, destinations, within=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in destinations) == supply[i]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(destinations, rule=demand_rule)

    def capacity_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.capacity_con = pyo.Constraint(origins, destinations, rule=capacity_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in destinations)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}