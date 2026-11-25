import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_factories = len(fixed_cost)
    n_months = len(demand)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_factories - 1)
    model.M = pyo.RangeSet(0, n_months - 1)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            fixed_cost[f] * mdl.run[f, t] + variable_cost[f] * mdl.prod[f, t]
            for f in mdl.F
            for t in mdl.M
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(mdl, f, t):
        return mdl.prod[f, t] >= min_production[f] * mdl.run[f, t]
    model.min_con = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(mdl, f, t):
        return mdl.prod[f, t] <= max_production[f] * mdl.run[f, t]
    model.max_con = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(mdl, t):
        return sum(mdl.prod[f, t] for f in mdl.F) >= demand[t]
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}