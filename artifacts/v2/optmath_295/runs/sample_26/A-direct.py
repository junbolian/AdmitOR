import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    n_prod = len(capacity)
    n_cont = len(demand)
    producers = range(n_prod)
    contracts = range(n_cont)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(producers, contracts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(producers, contracts, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in producers for j in contracts),
        sense=pyo.minimize,
    )

    model.cap = pyo.Constraint(
        producers,
        rule=lambda m, i: sum(m.x[i, j] for j in contracts) <= capacity[i],
    )

    model.dem = pyo.Constraint(
        contracts,
        rule=lambda m, j: sum(m.x[i, j] for i in producers) >= demand[j],
    )

    model.min_contrib = pyo.Constraint(
        contracts,
        rule=lambda m, j: sum(m.y[i, j] for i in producers) >= 2,
    )

    def link_lower(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]

    model.link_lower = pyo.Constraint(producers, contracts, rule=link_lower)

    def link_upper(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]

    model.link_upper = pyo.Constraint(producers, contracts, rule=link_upper)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}