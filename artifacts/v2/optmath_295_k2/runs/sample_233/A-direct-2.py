import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_producers = params["min_producers"]
    min_delivery = params["min_delivery"]

    producers = list(range(4))
    contracts = list(range(5))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)
    model.PC = pyo.Set(initialize=[(p, c) for p in producers for c in contracts], dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(md):
        return sum(cost[p][c] * md.x[p, c] for p in producers for c in contracts)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(md, p):
        return sum(md.x[p, c] for c in contracts) <= capacity[p]

    model.capacity_con = pyo.Constraint(model.P, rule=cap_rule)

    def demand_rule(md, c):
        return sum(md.x[p, c] for p in producers) >= demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def link_upper_rule(md, p, c):
        return md.x[p, c] <= capacity[p] * md.y[p, c]

    model.link_upper = pyo.Constraint(model.PC, rule=link_upper_rule)

    def link_lower_rule(md, p, c):
        return md.x[p, c] >= min_delivery[p] * md.y[p, c]

    model.link_lower = pyo.Constraint(model.PC, rule=link_lower_rule)

    def count_rule(md, c):
        return sum(md.y[p, c] for p in producers) >= min_producers[c]

    model.count_con = pyo.Constraint(model.C, rule=count_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}