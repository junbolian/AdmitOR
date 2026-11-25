import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fact = 5
    n_month = 4

    fixed_cost = params["fixed_cost"]
    var_cost = params["var_cost"]
    min_prod = params["min_prod"]
    max_prod = params["max_prod"]
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.fact = pyo.RangeSet(0, n_fact - 1)
    model.month = pyo.RangeSet(0, n_month - 1)

    model.operate = pyo.Var(model.fact, model.month, within=pyo.Binary)
    model.produce = pyo.Var(model.fact, model.month, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.operate[f, t] + var_cost[f] * m.produce[f, t]
            for f in m.fact for t in m.month
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(m, f, t):
        return m.produce[f, t] >= min_prod[f] * m.operate[f, t]
    model.min_constraint = pyo.Constraint(model.fact, model.month, rule=min_rule)

    def max_rule(m, f, t):
        return m.produce[f, t] <= max_prod[f] * m.operate[f, t]
    model.max_constraint = pyo.Constraint(model.fact, model.month, rule=max_rule)

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.fact) >= demand[t]
    model.demand_constraint = pyo.Constraint(model.month, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}