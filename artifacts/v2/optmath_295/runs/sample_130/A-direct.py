import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_producers = 4
    num_contracts = 5

    producers = range(num_producers)
    contracts = range(num_contracts)

    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(producers))
    model.C = pyo.Set(initialize=list(contracts))

    model.x = pyo.Var(model.P, model.C, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, within=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.C)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]
    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def min_contrib_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= 2
    model.min_contrib_con = pyo.Constraint(model.C, rule=min_contrib_rule)

    def link_upper_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]
    model.link_upper_con = pyo.Constraint(model.P, model.C, rule=link_upper_rule)

    def link_lower_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.link_lower_con = pyo.Constraint(model.P, model.C, rule=link_lower_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}