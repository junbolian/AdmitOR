import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)

    centers = range(num_centers)
    stores = range(num_stores)

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers)
    model.stores = pyo.Set(initialize=stores)

    model.open_center = pyo.Var(model.centers, within=pyo.Binary)
    model.flow = pyo.Var(model.centers, model.stores, within=pyo.NonNegativeReals)

    def objective_rule(m):
        opening = sum(opening_cost[i] * m.open_center[i] for i in m.centers)
        transport = sum(
            transport_cost[i][j] * m.flow[i, j]
            for i in m.centers
            for j in m.stores
        )
        return opening + transport

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.centers) == demand[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in m.stores) <= capacity[i] * m.open_center[i]

    model.capacity_con = pyo.Constraint(model.centers, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}