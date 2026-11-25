import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    monthly_demand = params["monthly_demand"]

    factories = list(range(3))
    months = list(range(4))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.run[f, t] + variable_cost[f] * m.prod[f, t]
            for f in m.F
            for t in m.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, f, t):
        return m.prod[f, t] >= min_production[f] * m.run[f, t]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(m, f, t):
        return m.prod[f, t] <= max_production[f] * m.run[f, t]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= monthly_demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}