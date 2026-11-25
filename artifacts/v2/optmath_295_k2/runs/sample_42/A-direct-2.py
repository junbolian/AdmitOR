import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    supply = params["supply"]
    demand = params["demand"]
    capacity = params["capacity"]

    origins = list(range(4))
    dests = list(range(5))
    prods = list(range(2))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=prods)
    model.O = pyo.Set(initialize=origins)
    model.D = pyo.Set(initialize=dests)

    model.cost_param = pyo.Param(
        model.P, model.O, model.D,
        initialize={(p, o, d): cost[p][o][d] for p in prods for o in origins for d in dests},
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.P, model.O, model.D, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            m.cost_param[p, o, d] * m.x[p, o, d]
            for p in m.P for o in m.O for d in m.D
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, p, o):
        return sum(m.x[p, o, d] for d in m.D) <= supply[p][o]
    model.supply_con = pyo.Constraint(model.P, model.O, rule=supply_rule)

    def demand_rule(m, p, d):
        return sum(m.x[p, o, d] for o in m.O) == demand[p][d]
    model.demand_con = pyo.Constraint(model.P, model.D, rule=demand_rule)

    def cap_rule(m, o, d):
        return sum(m.x[p, o, d] for p in m.P) <= capacity[o][d]
    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}