import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = len(fixed_cost)
    num_months = len(demand)
    factories = range(num_factories)
    months = range(num_months)

    model = pyo.ConcreteModel()

    model.FACTORIES = pyo.Set(initialize=list(factories))
    model.MONTHS = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.FACTORIES, model.MONTHS, domain=pyo.Binary)
    model.produce = pyo.Var(model.FACTORIES, model.MONTHS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.run[f, t] + variable_cost[f] * m.produce[f, t]
            for f in m.FACTORIES
            for t in m.MONTHS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, f, t):
        return m.produce[f, t] >= min_production[f] * m.run[f, t]

    model.min_prod_con = pyo.Constraint(model.FACTORIES, model.MONTHS, rule=min_prod_rule)

    def max_prod_rule(m, f, t):
        return m.produce[f, t] <= max_production[f] * m.run[f, t]

    model.max_prod_con = pyo.Constraint(model.FACTORIES, model.MONTHS, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.FACTORIES) >= demand[t]

    model.demand_con = pyo.Constraint(model.MONTHS, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}