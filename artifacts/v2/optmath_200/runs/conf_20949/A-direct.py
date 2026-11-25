import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_fact = len(fixed_cost)
    n_month = len(demand)
    factories = range(n_fact)
    months = range(n_month)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.run[f, t] + variable_cost[f] * m.prod[f, t]
            for f in m.F for t in m.M
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(m, f, t):
        return m.prod[f, t] >= min_production[f] * m.run[f, t]
    model.c_min = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(m, f, t):
        return m.prod[f, t] <= max_production[f] * m.run[f, t]
    model.c_max = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= demand[t]
    model.c_demand = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}