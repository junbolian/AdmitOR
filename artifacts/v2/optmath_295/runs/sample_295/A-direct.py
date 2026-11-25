import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    six_factories = range(6)
    six_months = range(6)

    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    model = pyo.ConcreteModel()

    model.FACTORIES = pyo.Set(initialize=list(six_factories))
    model.MONTHS = pyo.Set(initialize=list(six_months))

    model.run = pyo.Var(model.FACTORIES, model.MONTHS, domain=pyo.Binary)
    model.produce = pyo.Var(model.FACTORIES, model.MONTHS, domain=pyo.NonNegativeReals)

    def min_prod_rule(m, f, t):
        return m.produce[f, t] >= min_production[f] * m.run[f, t]

    def max_prod_rule(m, f, t):
        return m.produce[f, t] <= max_production[f] * m.run[f, t]

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.FACTORIES) >= demand[t]

    model.min_prod_con = pyo.Constraint(model.FACTORIES, model.MONTHS, rule=min_prod_rule)
    model.max_prod_con = pyo.Constraint(model.FACTORIES, model.MONTHS, rule=max_prod_rule)
    model.demand_con = pyo.Constraint(model.MONTHS, rule=demand_rule)

    def total_cost(m):
        fixed = sum(fixed_cost[f] * m.run[f, t] for f in m.FACTORIES for t in m.MONTHS)
        variable = sum(variable_cost[f] * m.produce[f, t] for f in m.FACTORIES for t in m.MONTHS)
        return fixed + variable

    model.total_cost = pyo.Objective(rule=total_cost, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}