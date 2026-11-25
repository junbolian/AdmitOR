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

    model = pyo.ConcreteModel()

    model.FACT = pyo.RangeSet(0, num_factories - 1)
    model.MONTH = pyo.RangeSet(0, num_months - 1)

    model.y = pyo.Var(model.FACT, model.MONTH, domain=pyo.Binary)
    model.x = pyo.Var(model.FACT, model.MONTH, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            fixed_cost[f] * m.y[f, t] + variable_cost[f] * m.x[f, t]
            for f in m.FACT
            for t in m.MONTH
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, f, t):
        return m.x[f, t] >= min_production[f] * m.y[f, t]

    model.min_prod_con = pyo.Constraint(model.FACT, model.MONTH, rule=min_prod_rule)

    def max_prod_rule(m, f, t):
        return m.x[f, t] <= max_production[f] * m.y[f, t]

    model.max_prod_con = pyo.Constraint(model.FACT, model.MONTH, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.x[f, t] for f in m.FACT) >= demand[t]

    model.demand_con = pyo.Constraint(model.MONTH, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}