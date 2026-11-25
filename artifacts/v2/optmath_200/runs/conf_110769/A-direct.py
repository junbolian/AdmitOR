import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    var_cost = params["var_cost"]
    min_prod = params["min_prod"]
    max_capacity = params["max_capacity"]
    demand = params["demand"]

    n_fact = len(fixed_cost)
    n_month = len(demand)

    model = pyo.ConcreteModel()

    model.FACT = pyo.RangeSet(0, n_fact - 1)
    model.MONTH = pyo.RangeSet(0, n_month - 1)

    model.y = pyo.Var(model.MONTH, model.FACT, domain=pyo.Binary)
    model.x = pyo.Var(model.MONTH, model.FACT, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[j] * m.y[t, j] + var_cost[j] * m.x[t, j]
            for t in m.MONTH
            for j in m.FACT
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, t, j):
        return m.x[t, j] >= min_prod[j] * m.y[t, j]

    model.min_prod_con = pyo.Constraint(model.MONTH, model.FACT, rule=min_prod_rule)

    def max_prod_rule(m, t, j):
        return m.x[t, j] <= max_capacity[j] * m.y[t, j]

    model.max_prod_con = pyo.Constraint(model.MONTH, model.FACT, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.x[t, j] for j in m.FACT) >= demand[t]

    model.demand_con = pyo.Constraint(model.MONTH, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}