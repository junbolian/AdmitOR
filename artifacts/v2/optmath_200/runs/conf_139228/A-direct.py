import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]
    capacity = params["capacity"]

    facilities = list(range(len(fixed_cost)))
    customers = list(range(len(demand)))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facilities)
    model.C = pyo.Set(initialize=customers)

    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.F, domain=pyo.Binary)

    def obj_rule(m):
        return (
            sum(fixed_cost[f] * m.y[f] for f in m.F)
            + sum(shipping_cost[f][c] * m.x[f, c] for f in m.F for c in m.C)
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.x[f, c] for f in m.F) == demand[c]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(m, f):
        return sum(m.x[f, c] for c in m.C) <= capacity[f] * m.y[f]
    model.capacity_con = pyo.Constraint(model.F, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}