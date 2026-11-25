import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    n_producers = len(capacity)
    n_contracts = len(demand)
    producers = list(range(n_producers))
    contracts = list(range(n_contracts))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    # x[i, j]: amount producer i delivers to contract j
    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)

    # y[i, j]: binary, whether producer i contributes to contract j
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Link x and y with minimum delivery requirement
    def min_delivery_rule(model, i, j):
        return model.x[i, j] >= min_delivery[i] * model.y[i, j]

    model.min_delivery_con = pyo.Constraint(model.P, model.C, rule=min_delivery_rule)

    # Capacity constraint per producer
    def capacity_rule(model, i):
        return sum(model.x[i, j] for j in model.C) <= capacity[i]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    # Demand constraint per contract
    def demand_rule(model, j):
        return sum(model.x[i, j] for i in model.P) >= demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    # Minimum contributors per contract
    def contributors_rule(model, j):
        return sum(model.y[i, j] for i in model.P) >= min_contributors[j]

    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    # Objective: minimize total production cost
    def obj_rule(model):
        return sum(cost[i][j] * model.x[i, j] for i in model.P for j in model.C)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}