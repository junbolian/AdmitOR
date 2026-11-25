import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_fact = 5
    n_month = 6
    fact = list(range(n_fact))
    month = list(range(n_month))

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.FACT = pyo.Set(initialize=fact)
    model.MONTH = pyo.Set(initialize=month)

    model.run = pyo.Var(model.FACT, model.MONTH, domain=pyo.Binary)
    model.prod = pyo.Var(model.FACT, model.MONTH, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            fixed_cost[i] * mdl.run[i, t] + variable_cost[i] * mdl.prod[i, t]
            for i in mdl.FACT
            for t in mdl.MONTH
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(mdl, i, t):
        return mdl.prod[i, t] >= min_production[i] * mdl.run[i, t]
    model.min_con = pyo.Constraint(model.FACT, model.MONTH, rule=min_rule)

    def max_rule(mdl, i, t):
        return mdl.prod[i, t] <= max_production[i] * mdl.run[i, t]
    model.max_con = pyo.Constraint(model.FACT, model.MONTH, rule=max_rule)

    def demand_rule(mdl, t):
        return sum(mdl.prod[i, t] for i in mdl.FACT) >= demand[t]
    model.demand_con = pyo.Constraint(model.MONTH, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}