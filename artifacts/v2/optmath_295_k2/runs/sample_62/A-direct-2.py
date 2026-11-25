import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_factories = 6
    n_months = 5
    factories = list(range(n_factories))
    months = list(range(n_months))

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[i] * m.run[i, j] + variable_cost[i] * m.prod[i, j]
            for i in m.F for j in m.M
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(m, i, j):
        return m.prod[i, j] >= min_production[i] * m.run[i, j]
    model.min_con = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(m, i, j):
        return m.prod[i, j] <= max_production[i] * m.run[i, j]
    model.max_con = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(m, j):
        return sum(m.prod[i, j] for i in m.F) >= demand[j]
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}