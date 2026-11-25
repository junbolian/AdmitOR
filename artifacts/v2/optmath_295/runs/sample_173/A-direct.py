import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_max = params["producer_max"]
    demand = params["contract_demand"]
    min_prod = params["min_producers_per_contract"]
    min_delivery = params["min_delivery_per_producer"]
    cost = params["production_cost"]

    n_prod = len(producer_max)
    n_cont = len(demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_prod - 1)
    model.C = pyo.RangeSet(0, n_cont - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= producer_max[p]
    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    def dem_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= demand[c]
    model.dem = pyo.Constraint(model.C, rule=dem_rule)

    def nprod_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= min_prod
    model.nprod = pyo.Constraint(model.C, rule=nprod_rule)

    def upper_rule(m, p, c):
        return m.x[p, c] <= producer_max[p] * m.y[p, c]
    model.upper = pyo.Constraint(model.P, model.C, rule=upper_rule)

    def lower_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]
    model.lower = pyo.Constraint(model.P, model.C, rule=lower_rule)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}