import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost = params["shipping_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(fixed_cost)
    n_store = len(demand)

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, n_dc - 1)
    model.STORE = pyo.RangeSet(0, n_store - 1)

    model.open = pyo.Var(model.DC, domain=pyo.Binary)
    model.ship = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[i] * m.open[i] for i in m.DC) + sum(
            shipping_cost[i][j] * m.ship[i, j]
            for i in m.DC
            for j in m.STORE
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.DC) == demand[j]
    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.ship[i, j] for j in m.STORE) <= capacity[i] * m.open[i]
    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": str(exc) or "infeasible"}