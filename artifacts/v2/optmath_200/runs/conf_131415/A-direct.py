import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_origins = 4
    num_destinations = 6
    origins = list(range(num_origins))
    destinations = list(range(num_destinations))

    supply = {
        0: {o: params["supply_p0"][o] for o in origins},
        1: {o: params["supply_p1"][o] for o in origins},
    }
    demand = {
        0: {d: params["demand_p0"][d] for d in destinations},
        1: {d: params["demand_p1"][d] for d in destinations},
    }
    cost = {
        0: {(o, d): params["cost_p0"][o][d] for o in origins for d in destinations},
        1: {(o, d): params["cost_p1"][o][d] for o in origins for d in destinations},
    }
    cap = {(o, d): params["route_capacity"][o][d] for o in origins for d in destinations}

    model = pyo.ConcreteModel()

    model.ORIGINS = pyo.Set(initialize=origins)
    model.DESTINATIONS = pyo.Set(initialize=destinations)
    model.PRODUCTS = pyo.Set(initialize=[0, 1])

    model.x = pyo.Var(
        model.PRODUCTS, model.ORIGINS, model.DESTINATIONS,
        domain=pyo.NonNegativeReals,
    )

    def obj_rule(m):
        return sum(
            cost[p][(o, d)] * m.x[p, o, d]
            for p in m.PRODUCTS
            for o in m.ORIGINS
            for d in m.DESTINATIONS
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, p, o):
        return sum(m.x[p, o, d] for d in m.DESTINATIONS) <= supply[p][o]
    model.supply_con = pyo.Constraint(model.PRODUCTS, model.ORIGINS, rule=supply_rule)

    def demand_rule(m, p, d):
        return sum(m.x[p, o, d] for o in m.ORIGINS) >= demand[p][d]
    model.demand_con = pyo.Constraint(model.PRODUCTS, model.DESTINATIONS, rule=demand_rule)

    def route_cap_rule(m, o, d):
        return sum(m.x[p, o, d] for p in m.PRODUCTS) <= cap[(o, d)]
    model.route_cap_con = pyo.Constraint(model.ORIGINS, model.DESTINATIONS, rule=route_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}