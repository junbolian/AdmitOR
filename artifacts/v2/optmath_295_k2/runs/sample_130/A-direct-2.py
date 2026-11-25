import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_producers = 4
    n_contracts = 5
    producers = list(range(n_producers))
    contracts = list(range(n_contracts))

    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(mdl, p):
        return sum(mdl.x[p, c] for c in mdl.C) <= capacity[p]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(mdl, c):
        return sum(mdl.x[p, c] for p in mdl.P) >= demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def min_contributors_rule(mdl, c):
        return sum(mdl.y[p, c] for p in mdl.P) >= 2

    model.min_contributors_con = pyo.Constraint(model.C, rule=min_contributors_rule)

    def min_delivery_rule(mdl, p, c):
        return mdl.x[p, c] >= min_delivery[p] * mdl.y[p, c]

    model.min_delivery_con = pyo.Constraint(model.P, model.C, rule=min_delivery_rule)

    def link_rule(mdl, p, c):
        return mdl.x[p, c] <= capacity[p] * mdl.y[p, c]

    model.link_con = pyo.Constraint(model.P, model.C, rule=link_rule)

    def obj_rule(mdl):
        return sum(cost[p][c] * mdl.x[p, c] for p in mdl.P for c in mdl.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}