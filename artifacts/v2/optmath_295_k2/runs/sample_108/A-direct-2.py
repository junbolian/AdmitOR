import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producers = ["P0", "P1", "P2"]
    contracts = ["C0", "C1", "C2", "C3"]
    p_idx = {p: i for i, p in enumerate(producers)}
    c_idx = {c: j for j, c in enumerate(contracts)}

    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers, ordered=True)
    model.C = pyo.Set(initialize=contracts, ordered=True)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(
            cost[p_idx[p]][c_idx[c]] * mdl.x[p, c]
            for p in mdl.P
            for c in mdl.C
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(mdl, p):
        return sum(mdl.x[p, c] for c in mdl.C) <= capacity[p_idx[p]]

    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    def demand_rule(mdl, c):
        return sum(mdl.x[p, c] for p in mdl.P) >= demand[c_idx[c]]

    model.demand = pyo.Constraint(model.C, rule=demand_rule)

    def min_contrib_rule(mdl, c):
        return sum(mdl.y[p, c] for p in mdl.P) >= 2

    model.min_contrib = pyo.Constraint(model.C, rule=min_contrib_rule)

    def link_ub_rule(mdl, p, c):
        return mdl.x[p, c] <= capacity[p_idx[p]] * mdl.y[p, c]

    model.link_ub = pyo.Constraint(model.P, model.C, rule=link_ub_rule)

    def min_delivery_rule(mdl, p, c):
        return mdl.x[p, c] >= min_delivery[p_idx[p]] * mdl.y[p, c]

    model.min_delivery = pyo.Constraint(model.P, model.C, rule=min_delivery_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}