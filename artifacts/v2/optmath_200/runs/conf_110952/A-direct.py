import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    n_origins = len(supply)
    n_destinations = len(demand)
    n_products = len(supply[0])

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.destinations = pyo.RangeSet(0, n_destinations - 1)
    model.products = pyo.RangeSet(0, n_products - 1)

    model.x = pyo.Var(
        model.origins, model.destinations, model.products,
        domain=pyo.NonNegativeReals,
    )

    def obj_rule(m):
        return sum(
            cost[i][j][k] * m.x[i, j, k]
            for i in m.origins
            for j in m.destinations
            for k in m.products
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i, k):
        return sum(m.x[i, j, k] for j in m.destinations) <= supply[i][k]
    model.supply_con = pyo.Constraint(model.origins, model.products, rule=supply_rule)

    def demand_rule(m, j, k):
        return sum(m.x[i, j, k] for i in m.origins) >= demand[j][k]
    model.demand_con = pyo.Constraint(model.destinations, model.products, rule=demand_rule)

    def limit_rule(m, i, j):
        return sum(m.x[i, j, k] for k in m.products) <= limit[i][j]
    model.limit_con = pyo.Constraint(model.origins, model.destinations, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}