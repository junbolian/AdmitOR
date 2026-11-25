import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    contract_demand = params["contract_demand"]
    min_delivery = params["min_delivery"]
    min_producers_per_contract = params["min_producers_per_contract"]

    n_prod = len(capacity)
    n_cont = len(contract_demand)
    producers = range(n_prod)
    contracts = range(n_cont)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(producers))
    model.C = pyo.Set(initialize=list(contracts))

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= capacity[p]

    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= contract_demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def link_lo_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]

    model.link_lo_con = pyo.Constraint(model.P, model.C, rule=link_lo_rule)

    def link_hi_rule(m, p, c):
        ub = min(capacity[p], contract_demand[c])
        return m.x[p, c] <= ub * m.y[p, c]

    model.link_hi_con = pyo.Constraint(model.P, model.C, rule=link_hi_rule)

    def nprod_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= min_producers_per_contract

    model.nprod_con = pyo.Constraint(model.C, rule=nprod_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}