import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fact = 6
    n_month = 4

    min_prod = params["min_production"]
    max_prod = params["max_production"]
    demand = params["monthly_demand"]
    fixed_cost = params["fixed_cost"]
    var_cost = params["variable_cost"]

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, n_fact - 1)
    model.M = pyo.RangeSet(0, n_month - 1)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def min_rule(m, f, t):
        return m.prod[f, t] >= min_prod[f] * m.run[f, t]

    def max_rule(m, f, t):
        return m.prod[f, t] <= max_prod[f] * m.run[f, t]

    model.min_con = pyo.Constraint(model.F, model.M, rule=min_rule)
    model.max_con = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.run[f, t] + var_cost[f] * m.prod[f, t]
            for f in m.F
            for t in m.M
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}