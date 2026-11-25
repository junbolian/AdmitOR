import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_producers = 4
    num_contracts = 5
    producers = list(range(num_producers))
    contracts = list(range(num_contracts))

    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)
    model.PC = pyo.Set(initialize=[(p, c) for p in producers for c in contracts])

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def capacity_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= capacity[p]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def min_contrib_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= 2

    model.min_contrib_con = pyo.Constraint(model.C, rule=min_contrib_rule)

    def link_lower_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]

    model.link_lower_con = pyo.Constraint(model.PC, rule=link_lower_rule)

    def link_upper_rule(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]

    model.link_upper_con = pyo.Constraint(model.PC, rule=link_upper_rule)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p, c in m.PC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}