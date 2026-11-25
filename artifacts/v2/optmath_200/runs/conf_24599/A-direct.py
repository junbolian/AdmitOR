import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fact = 4
    n_months = 6
    factories = list(range(n_fact))
    months = list(range(n_months))

    fixed_cost = params["fixed_cost"]
    var_cost = params["var_cost"]
    min_prod = params["min_prod"]
    max_prod = params["max_prod"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def min_rule(mdl, f, t):
        return mdl.produce[f, t] >= min_prod[f] * mdl.run[f, t]

    def max_rule(mdl, f, t):
        return mdl.produce[f, t] <= max_prod[f] * mdl.run[f, t]

    model.min_con = pyo.Constraint(model.F, model.M, rule=min_rule)
    model.max_con = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(mdl, t):
        return sum(mdl.produce[f, t] for f in mdl.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def obj_rule(mdl):
        return sum(
            fixed_cost[f] * mdl.run[f, t] + var_cost[f] * mdl.produce[f, t]
            for f in mdl.F
            for t in mdl.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}