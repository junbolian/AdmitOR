import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]
    min_producers = params["min_producers"]

    n_prod = len(capacity)
    n_cont = len(demand)

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, n_prod - 1)
    model.J = pyo.RangeSet(0, n_cont - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.cap_con = pyo.Constraint(
        model.I,
        rule=lambda m, i: sum(m.x[i, j] for j in m.J) <= capacity[i],
    )

    model.demand_con = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.x[i, j] for i in m.I) >= demand[j],
    )

    model.minprod_con = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.y[i, j] for i in m.I) >= min_producers[j],
    )

    model.link_lo = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda m, i, j: m.x[i, j] >= min_delivery[i] * m.y[i, j],
    )

    model.link_hi = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda m, i, j: m.x[i, j] <= capacity[i] * m.y[i, j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}