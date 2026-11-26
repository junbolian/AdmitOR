import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dc = len(opening_cost)
    num_store = len(demand)

    dc_idx = list(range(num_dc))
    store_idx = list(range(num_store))

    model = pyo.ConcreteModel()

    model.DC = pyo.Set(initialize=dc_idx)
    model.STORE = pyo.Set(initialize=store_idx)

    model.open = pyo.Var(model.DC, domain=pyo.Binary)
    model.ship = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def transport_expr(m):
        return sum(
            transport_cost[i][j] * m.ship[i, j]
            for i in m.DC for j in m.STORE
        )

    model.transport_total = pyo.Expression(rule=transport_expr)

    def opening_expr(m):
        return sum(opening_cost[i] * m.open[i] for i in m.DC)

    model.opening_total = pyo.Expression(rule=opening_expr)

    model.total_cost = pyo.Expression(
        expr=model.opening_total + model.transport_total
    )

    model.obj = pyo.Objective(expr=model.total_cost, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.DC) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.ship[i, j] for j in m.STORE) <= capacity[i] * m.open[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}