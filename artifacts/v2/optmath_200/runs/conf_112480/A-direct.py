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

    model.FACTORIES = pyo.RangeSet(0, n_factories - 1)
    model.MONTHS = pyo.RangeSet(0, n_months - 1)

    model.run = pyo.Var(model.MONTHS, model.FACTORIES, domain=pyo.Binary)
    model.produce = pyo.Var(model.MONTHS, model.FACTORIES, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.run[t, f] + variable_cost[f] * m.produce[t, f]
            for t in m.MONTHS
            for f in m.FACTORIES
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(m, t, f):
        return m.produce[t, f] >= min_production[f] * m.run[t, f]

    model.min_constraint = pyo.Constraint(model.MONTHS, model.FACTORIES, rule=min_rule)

    def max_rule(m, t, f):
        return m.produce[t, f] <= max_production[f] * m.run[t, f]

    model.max_constraint = pyo.Constraint(model.MONTHS, model.FACTORIES, rule=max_rule)

    def demand_rule(m, t):
        return sum(m.produce[t, f] for f in m.FACTORIES) >= demand[t]

    model.demand_constraint = pyo.Constraint(model.MONTHS, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}