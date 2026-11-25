import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = list(range(n_orig))
    dests = list(range(n_dest))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(origins, dests, bounds=lambda m, i, j: (0, capacity[i][j]))

    model.cost_expr = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in origins for j in dests),
        sense=pyo.minimize,
    )

    model.supply_rule = pyo.Constraint(
        origins, rule=lambda m, i: sum(m.x[i, j] for j in dests) == supply[i]
    )
    model.demand_rule = pyo.Constraint(
        dests, rule=lambda m, j: sum(m.x[i, j] for i in origins) == demand[j]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost_expr))
    return {"objective": obj_val, "status": "optimal"}