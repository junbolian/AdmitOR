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

    model.open = pyo.Var(model.DC, domain=pyo.Binary)
    model.flow = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def transport_rule(m, i, j):
        return m.flow[i, j]

    model.transport_expr = pyo.Expression(model.DC, model.STORE, rule=transport_rule)

    def open_rule(m, i):
        return opening_cost[i] * m.open[i]

    model.open_expr = pyo.Expression(model.DC, rule=open_rule)

    def transport_cost_rule(m, i, j):
        return transport_cost[i][j] * m.flow[i, j]

    model.transport_cost_expr = pyo.Expression(model.DC, model.STORE, rule=transport_cost_rule)

    model.obj = pyo.Objective(
        expr=sum(model.open_expr[i] for i in model.DC)
        + sum(model.transport_cost_expr[i, j] for i in model.DC for j in model.STORE),
        sense=pyo.minimize,
    )

    def demand_rule(m, j):
        return sum(m.flow[i, j] for i in m.DC) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.flow[i, j] for j in m.STORE) <= capacity[i] * m.open[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}