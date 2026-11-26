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

    model.y = pyo.Var(model.DC, domain=pyo.Binary)
    model.x = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def _transport_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j]
                   for i in m.DC for j in m.STORE)

    model.transport_expr = pyo.Expression(rule=_transport_rule)

    def _opening_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in m.DC)

    model.opening_expr = pyo.Expression(rule=_opening_rule)

    model.total_cost = pyo.Objective(
        expr=model.transport_expr + model.opening_expr,
        sense=pyo.minimize,
    )

    def _demand_rule(m, j):
        return sum(m.x[i, j] for i in m.DC) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=_demand_rule)

    def _capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.STORE) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=_capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}