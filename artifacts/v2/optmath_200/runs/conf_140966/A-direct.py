import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = len(fixed_cost)
    num_months = len(demand)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, num_factories - 1)
    model.M = pyo.RangeSet(0, num_months - 1)

    model.run = pyo.Var(model.M, model.F, domain=pyo.Binary)
    model.produce = pyo.Var(model.M, model.F, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[j] * m.run[i, j] + variable_cost[j] * m.produce[i, j]
            for i in m.M
            for j in m.F
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, i, j):
        return m.produce[i, j] >= min_production[j] * m.run[i, j]

    model.min_prod_con = pyo.Constraint(model.M, model.F, rule=min_prod_rule)

    def max_prod_rule(m, i, j):
        return m.produce[i, j] <= max_production[j] * m.run[i, j]

    model.max_prod_con = pyo.Constraint(model.M, model.F, rule=max_prod_rule)

    def demand_rule(m, i):
        return sum(m.produce[i, j] for j in m.F) >= demand[i]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}