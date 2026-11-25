import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_origins = len(supply)
    num_destinations = len(demand)

    origins = list(range(num_origins))
    destinations = list(range(num_destinations))

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins)
    model.destinations = pyo.Set(initialize=destinations)

    model.x = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def objective_rule(m):
        return sum(
            cost[i][j] * m.x[i, j]
            for i in m.origins
            for j in m.destinations
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.destinations) == supply[i]

    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) == demand[j]

    model.demand_constraint = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    def capacity_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.capacity_constraint = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}