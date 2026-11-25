import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    num_producers = len(capacity)
    num_contracts = len(demand)

    producers = range(num_producers)
    contracts = range(num_contracts)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(producers))
    model.C = pyo.Set(initialize=list(contracts))

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def contributors_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_contributors

    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    def linking_lower_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]

    model.linking_lower_con = pyo.Constraint(
        model.P, model.C, rule=linking_lower_rule
    )

    def linking_upper_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]

    model.linking_upper_con = pyo.Constraint(
        model.P, model.C, rule=linking_upper_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}