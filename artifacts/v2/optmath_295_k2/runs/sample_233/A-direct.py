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

    # x[i,j]: amount produced by producer i for contract j (continuous)
    # y[i,j]: binary, 1 if producer i assigned to contract j
    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Objective: minimize total production cost
    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.C)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Capacity: total production of producer i across all contracts <= capacity
    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]
    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    # Demand: each contract receives at least its required amount
    def dem_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]
    model.dem_con = pyo.Constraint(model.C, rule=dem_rule)

    # Min producers: at least min_producers[j] producers assigned to contract j
    def minprod_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_producers[j]
    model.minprod_con = pyo.Constraint(model.C, rule=minprod_rule)

    # Linking: x[i,j] <= capacity[i] * y[i,j]
    def link_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]
    model.link_con = pyo.Constraint(model.P, model.C, rule=link_rule)

    # Min delivery: if assigned, deliver at least min_delivery[i]
    def mindel_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.mindel_con = pyo.Constraint(model.P, model.C, rule=mindel_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}