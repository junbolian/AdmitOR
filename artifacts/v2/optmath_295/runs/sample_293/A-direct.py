import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    transport_cost = params["transport_cost"]
    supply = params["supply"]
    demand = params["demand"]

    num_origins = len(supply)
    num_destinations = len(demand)

    origins = list(range(num_origins))
    destinations = list(range(num_destinations))

    cost = {}
    for i in origins:
        for j in destinations:
            cost[i, j] = transport_cost[i][j]

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins)
    model.destinations = pyo.Set(initialize=destinations)

    model.x = pyo.Var(model.origins, model.destinations, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i, j] * model.x[i, j]
                 for i in model.origins for j in model.destinations),
        sense=pyo.minimize,
    )

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.destinations) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.origins) == demand[j]

    model.supply_constraint = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_constraint = pyo.Constraint(model.destinations, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}