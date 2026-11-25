import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_factories = 6
    n_months = 6

    factories = range(n_factories)
    months = range(n_months)

    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def min_prod_rule(mdl, f, t):
        return mdl.produce[f, t] >= min_production[f] * mdl.run[f, t]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(mdl, f, t):
        return mdl.produce[f, t] <= max_production[f] * mdl.run[f, t]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(mdl, t):
        return sum(mdl.produce[f, t] for f in mdl.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def obj_rule(mdl):
        return sum(
            fixed_cost[f] * mdl.run[f, t] + variable_cost[f] * mdl.produce[f, t]
            for f in mdl.F
            for t in mdl.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}