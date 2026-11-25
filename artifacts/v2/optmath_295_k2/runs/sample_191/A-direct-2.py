import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fact = 6
    n_month = 5
    factories = list(range(n_fact))
    months = list(range(n_month))

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

    def obj_rule(mdl):
        return sum(
            fixed_cost[i] * mdl.run[i, j] + variable_cost[i] * mdl.prod[i, j]
            for i in mdl.F for j in mdl.M
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(mdl, i, j):
        return mdl.prod[i, j] >= min_production[i] * mdl.run[i, j]
    model.c_min = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(mdl, i, j):
        return mdl.prod[i, j] <= max_production[i] * mdl.run[i, j]
    model.c_max = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(mdl, j):
        return sum(mdl.prod[i, j] for i in mdl.F) >= demand[j]
    model.c_demand = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}