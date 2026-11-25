import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_origins = params["num_origins"]
    num_destinations = params["num_destinations"]
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    origins = list(range(num_origins))
    destinations = list(range(num_destinations))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, destinations, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in origins for j in destinations)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in destinations) == supply[i]

    model.supply_con = pyo.Constraint(origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in origins) == demand[j]

    model.demand_con = pyo.Constraint(destinations, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(origins, destinations, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}