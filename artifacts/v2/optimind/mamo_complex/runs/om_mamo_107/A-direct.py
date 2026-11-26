import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = 7
    n_store = 6
    dcs = list(range(1, n_dc + 1))
    stores = list(range(1, n_store + 1))
    arcs = [(i, j) for i in dcs for j in stores]

    model = pyo.ConcreteModel()

    model.y = pyo.Var(dcs, domain=pyo.Binary)
    model.x = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        open_part = sum(opening_cost[i - 1] * m.y[i] for i in dcs)
        trans_part = sum(
            transport_cost[i - 1][j - 1] * m.x[i, j] for i, j in arcs
        )
        return open_part + trans_part

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in dcs) == demand[j - 1]

    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in stores) <= capacity[i - 1] * m.y[i]

    model.capacity_con = pyo.Constraint(dcs, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}