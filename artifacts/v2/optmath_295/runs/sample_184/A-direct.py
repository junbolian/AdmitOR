import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_origins = 4
    num_destinations = 5
    num_products = 2

    origins = list(range(num_origins))
    destinations = list(range(num_destinations))
    products = list(range(num_products))

    model = pyo.ConcreteModel()

    model.O = pyo.Set(initialize=origins)
    model.D = pyo.Set(initialize=destinations)
    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.O, model.D, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            cost[o][d][p] * m.x[o, d, p]
            for o in m.O
            for d in m.D
            for p in m.P
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, o, p):
        return sum(m.x[o, d, p] for d in m.D) <= supply[o][p]

    model.supply_con = pyo.Constraint(model.O, model.P, rule=supply_rule)

    def demand_rule(m, d, p):
        return sum(m.x[o, d, p] for o in m.O) >= demand[d][p]

    model.demand_con = pyo.Constraint(model.D, model.P, rule=demand_rule)

    def cap_rule(m, o, d):
        return sum(m.x[o, d, p] for p in m.P) <= capacity[o][d]

    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}