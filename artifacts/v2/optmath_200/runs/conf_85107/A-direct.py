import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    cap = params["cap"]

    I = 7  # origins
    J = 7  # destinations
    P = 2  # products

    origins = range(I)
    dests = range(J)
    prods = range(P)

    model = pyo.ConcreteModel()

    # Decision variables: units of product p shipped from i to j
    model.x = pyo.Var(origins, dests, prods, domain=pyo.NonNegativeReals)

    # Objective: minimize total transportation cost
    model.total_cost = pyo.Objective(
        expr=sum(
            cost[i][j][p] * model.x[i, j, p]
            for i in origins
            for j in dests
            for p in prods
        ),
        sense=pyo.minimize,
    )

    # Supply constraints: full utilization of supply for each origin/product
    def supply_rule(mdl, i, p):
        return sum(mdl.x[i, j, p] for j in dests) == supply[i][p]

    model.supply_con = pyo.Constraint(origins, prods, rule=supply_rule)

    # Demand constraints: exactly meet demand at each destination/product
    def demand_rule(mdl, j, p):
        return sum(mdl.x[i, j, p] for i in origins) == demand[j][p]

    model.demand_con = pyo.Constraint(dests, prods, rule=demand_rule)

    # Capacity constraints: combined units of both products per origin-destination pair
    def cap_rule(mdl, i, j):
        return sum(mdl.x[i, j, p] for p in prods) <= cap[i][j]

    model.cap_con = pyo.Constraint(origins, dests, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}