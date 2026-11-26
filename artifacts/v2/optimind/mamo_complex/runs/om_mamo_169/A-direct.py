import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    centers = list(range(4))
    stores = list(range(8))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)

    # y[c] = 1 if center c is opened
    model.y = pyo.Var(model.C, within=pyo.Binary)
    # x[c,s] = units shipped from center c to store s
    model.x = pyo.Var(model.C, model.S, within=pyo.NonNegativeReals)

    def objective_rule(m):
        open_cost = sum(opening_cost[c] * m.y[c] for c in m.C)
        ship_cost = sum(transport_cost[c][s] * m.x[c, s] for c in m.C for s in m.S)
        return open_cost + ship_cost

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Each store's demand must be met
    def demand_rule(m, s):
        return sum(m.x[c, s] for c in m.C) == demand[s]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    # Shipments cannot exceed capacity of opened centers
    def capacity_rule(m, c):
        return sum(m.x[c, s] for s in m.S) <= capacity[c] * m.y[c]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}