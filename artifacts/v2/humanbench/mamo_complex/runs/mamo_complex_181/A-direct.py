import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    centers = list(range(1, 7))
    stores = list(range(1, 9))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=centers)
    model.J = pyo.Set(initialize=stores)

    model.y = pyo.Var(model.I, within=pyo.Binary)
    model.x = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)

    open_p = model.y
    flow_p = model.x

    def obj_rule(m):
        return sum(opening_cost[i - 1] * open_p[i] for i in m.I) + \
               sum(transport_cost[i - 1][j - 1] * flow_p[i, j]
                   for i in m.I for j in m.J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(flow_p[i, j] for i in m.I) >= demand[j - 1]
    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(flow_p[i, j] for j in m.J) <= capacity[i - 1] * open_p[i]
    model.capacity_con = pyo.Constraint(model.I, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}