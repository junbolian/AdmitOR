import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    n_fac = len(fixed_cost)
    n_cus = len(demand)

    model = pyo.ConcreteModel()

    model.FAC = pyo.RangeSet(0, n_fac - 1)
    model.CUS = pyo.RangeSet(0, n_cus - 1)

    model.x = pyo.Var(model.FAC, model.CUS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.FAC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_cost[f] * m.y[f] for f in m.FAC) + sum(
            shipping_cost[f][c] * m.x[f, c] for f in m.FAC for c in m.CUS
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.x[f, c] for f in m.FAC) == demand[c]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def cap_rule(m, f):
        return sum(m.x[f, c] for c in m.CUS) <= capacity[f] * m.y[f]

    model.cap_con = pyo.Constraint(model.FAC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}