import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    factories = list(range(4))
    months = list(range(5))

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories, ordered=True)
    model.M = pyo.Set(initialize=months, ordered=True)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[i] * m.run[i, j] + variable_cost[i] * m.produce[i, j]
            for i in m.F for j in m.M
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, i, j):
        return m.produce[i, j] >= min_production[i] * m.run[i, j]
    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(m, i, j):
        return m.produce[i, j] <= max_production[i] * m.run[i, j]
    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(m, j):
        return sum(m.produce[i, j] for i in m.F) >= demand[j]
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}