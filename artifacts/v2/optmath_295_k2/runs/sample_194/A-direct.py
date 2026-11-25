import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_orig = len(supply)
    n_dest = len(demand)
    origins = range(n_orig)
    dests = range(n_dest)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(
        [(i, j) for i in origins for j in dests],
        domain=pyo.NonNegativeReals,
    )

    model.cost_expr = pyo.Expression(
        expr=sum(cost[i][j] * model.x[i, j] for i in origins for j in dests)
    )
    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    model.supply_rule = pyo.Constraint(
        origins,
        rule=lambda m, i: sum(m.x[i, j] for j in dests) <= supply[i],
    )
    model.demand_rule = pyo.Constraint(
        dests,
        rule=lambda m, j: sum(m.x[i, j] for i in origins) >= demand[j],
    )
    model.cap_rule = pyo.Constraint(
        [(i, j) for i in origins for j in dests],
        rule=lambda m, i, j: m.x[i, j] <= capacity[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}