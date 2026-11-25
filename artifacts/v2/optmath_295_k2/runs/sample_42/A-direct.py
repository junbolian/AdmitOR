import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    supply = params["supply"]
    demand = params["demand"]
    capacity = params["capacity"]

    products = list(range(2))
    origins = list(range(4))
    destinations = list(range(5))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.O = pyo.Set(initialize=origins)
    model.D = pyo.Set(initialize=destinations)

    model.x = pyo.Var(model.P, model.O, model.D, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(
            cost[p][o][d] * model.x[p, o, d]
            for p in products for o in origins for d in destinations
        ),
        sense=pyo.minimize,
    )

    def supply_rule(mdl, p, o):
        return sum(mdl.x[p, o, d] for d in mdl.D) <= supply[p][o]
    model.supply_con = pyo.Constraint(model.P, model.O, rule=supply_rule)

    def demand_rule(mdl, p, d):
        return sum(mdl.x[p, o, d] for o in mdl.O) == demand[p][d]
    model.demand_con = pyo.Constraint(model.P, model.D, rule=demand_rule)

    def cap_rule(mdl, o, d):
        return sum(mdl.x[p, o, d] for p in mdl.P) <= capacity[o][d]
    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}