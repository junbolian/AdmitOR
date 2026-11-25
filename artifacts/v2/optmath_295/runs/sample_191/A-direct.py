import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    factories = list(range(6))
    months = list(range(5))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            fixed_cost[i] * mdl.run[i, t] + variable_cost[i] * mdl.prod[i, t]
            for i in mdl.F for t in mdl.M
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(mdl, i, t):
        return mdl.prod[i, t] >= min_production[i] * mdl.run[i, t]
    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(mdl, i, t):
        return mdl.prod[i, t] <= max_production[i] * mdl.run[i, t]
    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(mdl, t):
        return sum(mdl.prod[i, t] for i in mdl.F) >= demand[t]
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}