import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = 7
    num_stores = 9

    centers = list(range(num_centers))
    stores = list(range(num_stores))

    opening_costs = [
        params["opening_cost_center_1"],
        params["opening_cost_center_2"],
        params["opening_cost_center_3"],
        params["opening_cost_center_4"],
        params["opening_cost_center_5"],
        params["opening_cost_center_6"],
        params["opening_cost_center_7"],
    ]
    transport = params["transportation_cost_matrix"]
    demand = params["store_demand"]
    capacity = params["center_capacity"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)

    model.y = pyo.Var(model.C, domain=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_costs[i] * m.y[i] for i in m.C) + sum(
            transport[i][j] * m.x[i, j] for i in m.C for j in m.S
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.C) == demand[j]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.S) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}