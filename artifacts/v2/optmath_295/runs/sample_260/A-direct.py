import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    num_origins = params["num_origins"]
    num_destinations = params["num_destinations"]

    origins = list(range(num_origins))
    destinations = list(range(num_destinations))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, destinations, domain=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in destinations) == supply[i]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(destinations, rule=demand_rule)

    def objective_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in origins for j in destinations)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}