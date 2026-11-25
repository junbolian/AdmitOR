import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply_origin"]
    demand = params["demand_destination"]
    cost = params["cost_matrix"]
    capacity = params["capacity_matrix"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = list(range(n_orig))
    destinations = list(range(n_dest))

    model = pyo.ConcreteModel()
    model.origins = pyo.Set(initialize=origins)
    model.destinations = pyo.Set(initialize=destinations)
    model.links = pyo.Set(initialize=[(i, j) for i in origins for j in destinations])

    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    model.cost_expr = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in origins for j in destinations),
        sense=pyo.minimize,
    )

    model.supply_con = pyo.Constraint(
        model.origins,
        rule=lambda m, i: sum(m.x[i, j] for j in m.destinations) == supply[i],
    )
    model.demand_con = pyo.Constraint(
        model.destinations,
        rule=lambda m, j: sum(m.x[i, j] for i in m.origins) == demand[j],
    )
    model.capacity_con = pyo.Constraint(
        model.links,
        rule=lambda m, i, j: m.x[i, j] <= capacity[i][j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_expr))
    return {"objective": obj_val, "status": "optimal"}