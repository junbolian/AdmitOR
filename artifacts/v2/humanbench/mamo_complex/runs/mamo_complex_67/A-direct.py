import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_dc = 4
    n_store = 6
    dcs = list(range(n_dc))
    stores = list(range(n_store))

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.dcs = pyo.Set(initialize=dcs)
    model.stores = pyo.Set(initialize=stores)

    model.open_dc = pyo.Var(model.dcs, domain=pyo.Binary)
    model.flow = pyo.Var(model.dcs, model.stores, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return (
            sum(opening_cost[i] * m.open_dc[i] for i in m.dcs)
            + sum(transport_cost[i][j] * m.flow[i, j] for i in m.dcs for j in m.stores)
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.dcs) == demand[j]

    model.demand_con = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in m.stores) <= capacity[i] * m.open_dc[i]

    model.capacity_con = pyo.Constraint(model.dcs, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}