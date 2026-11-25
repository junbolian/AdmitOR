import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_factories = 5
    n_months = 4
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

    def fixed_rule(mdl, f, t):
        return fixed_cost[f][t]

    def variable_rule(mdl, f, t):
        return variable_cost[f]

    model.fixed_cost_c = pyo.Param(model.F, model.M, initialize=fixed_rule)
    model.variable_cost_c = pyo.Param(model.F, model.M, initialize=variable_rule)

    def obj_rule(mdl):
        return sum(
            mdl.fixed_cost_c[f, t] * mdl.run[f, t]
            + mdl.variable_cost_c[f, t] * mdl.prod[f, t]
            for f in mdl.F
            for t in mdl.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(mdl, f, t):
        return mdl.prod[f, t] >= min_production[f][t] * mdl.run[f, t]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(mdl, f, t):
        return mdl.prod[f, t] <= max_production[f][t] * mdl.run[f, t]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(mdl, t):
        return sum(mdl.prod[f, t] for f in mdl.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}