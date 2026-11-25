import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_origins = params["n_origins"]
    n_destinations = params["n_destinations"]
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    origins = list(range(n_origins))
    destinations = list(range(n_destinations))

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins)
    model.destinations = pyo.Set(initialize=destinations)

    model.x = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
        bounds=lambda m, i, j: (0, capacity[i][j]),
    )

    model.supply_constraint = pyo.Constraint(
        model.origins,
        rule=lambda m, i: sum(m.x[i, j] for j in m.destinations) == supply[i],
    )

    model.demand_constraint = pyo.Constraint(
        model.destinations,
        rule=lambda m, j: sum(m.x[i, j] for i in m.origins) == demand[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in origins for j in destinations),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}