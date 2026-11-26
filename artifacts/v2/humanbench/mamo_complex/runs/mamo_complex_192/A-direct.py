import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)
    centers = list(range(n_centers))
    stores = list(range(n_stores))

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers)
    model.stores = pyo.Set(initialize=stores)
    model.links = pyo.Set(initialize=[(i, j) for i in centers for j in stores],
                           dimen=2)

    model.is_open = pyo.Var(model.centers, within=pyo.Binary)
    model.flow = pyo.Var(model.links, within=pyo.NonNegativeReals)

    def opening_rule(m):
        return sum(opening_cost[i] * m.is_open[i] for i in m.centers)
    model.opening_expr = pyo.Expression(rule=opening_rule)

    def transport_rule(m):
        return sum(transport_cost[i][j] * m.flow[i, j] for (i, j) in m.links)
    model.transport_expr = pyo.Expression(rule=transport_rule)

    def obj_rule(m):
        return m.opening_expr + m.transport_expr
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.centers) == demand[j]
    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in m.stores) <= capacity[i] * m.is_open[i]
    model.capacity_con = pyo.Constraint(model.centers, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}