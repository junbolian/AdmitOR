import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    origins = list(range(len(supply)))
    destinations = list(range(len(demand)))
    products = list(range(len(supply[0])))

    model = pyo.ConcreteModel()

    model.ORIGINS = pyo.Set(initialize=origins)
    model.DESTINATIONS = pyo.Set(initialize=destinations)
    model.PRODUCTS = pyo.Set(initialize=products)
    model.LINKS = pyo.Set(
        initialize=[(o, d) for o in origins for d in destinations],
        dimen=2,
    )

    model.x = pyo.Var(
        model.ORIGINS,
        model.DESTINATIONS,
        model.PRODUCTS,
        domain=pyo.NonNegativeReals,
    )

    def obj_rule(m):
        return sum(
            cost[o][d][p] * m.x[o, d, p]
            for o in m.ORIGINS
            for d in m.DESTINATIONS
            for p in m.PRODUCTS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, o, p):
        return sum(m.x[o, d, p] for d in m.DESTINATIONS) == supply[o][p]

    model.supply_con = pyo.Constraint(
        model.ORIGINS, model.PRODUCTS, rule=supply_rule
    )

    def demand_rule(m, d, p):
        return sum(m.x[o, d, p] for o in m.ORIGINS) == demand[d][p]

    model.demand_con = pyo.Constraint(
        model.DESTINATIONS, model.PRODUCTS, rule=demand_rule
    )

    def capacity_rule(m, o, d):
        return sum(m.x[o, d, p] for p in m.PRODUCTS) <= capacity[o][d]

    model.capacity_con = pyo.Constraint(model.LINKS, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}