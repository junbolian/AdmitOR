import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(opening_cost)
    n_store = len(demand)

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, n_dc - 1)
    model.STORE = pyo.RangeSet(0, n_store - 1)
    model.LINK = pyo.Set(initialize=[(i, j) for i in range(n_dc) for j in range(n_store)])

    model.open_dc = pyo.Var(model.DC, domain=pyo.Binary)
    model.flow = pyo.Var(model.LINK, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return (sum(opening_cost[i] * m.open_dc[i] for i in range(n_dc))
                + sum(transport_cost[i][j] * m.flow[i, j] for i in range(n_dc) for j in range(n_store)))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in range(n_dc)) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in range(n_store)) <= capacity[i] * m.open_dc[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}