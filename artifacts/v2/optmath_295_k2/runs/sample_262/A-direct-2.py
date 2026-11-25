import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    ship_cost = params["ship_cost"]
    capacity = params["capacity"]

    facilities = list(range(4))
    customers = list(range(8))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facilities, ordered=True)
    model.C = pyo.Set(initialize=customers, ordered=True)

    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.F, domain=pyo.Binary)

    def demand_rule(mdl, c):
        return sum(mdl.x[f, c] for f in mdl.F) == demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(mdl, f):
        return sum(mdl.x[f, c] for c in mdl.C) <= capacity[f] * mdl.y[f]

    model.cap_con = pyo.Constraint(model.F, rule=cap_rule)

    def obj_rule(mdl):
        return sum(fixed_cost[f] * mdl.y[f] for f in mdl.F) + sum(
            ship_cost[f][c] * mdl.x[f, c] for f in mdl.F for c in mdl.C
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}