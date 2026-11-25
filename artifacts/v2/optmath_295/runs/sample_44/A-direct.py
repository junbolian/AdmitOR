import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    variable_costs = params["variable_costs"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = len(fixed_costs)
    num_months = len(demand)
    factories = range(num_factories)
    months = range(num_months)

    model = pyo.ConcreteModel()

    model.FACT = pyo.Set(initialize=list(factories))
    model.MONTH = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.FACT, model.MONTH, within=pyo.Binary)
    model.produce = pyo.Var(model.FACT, model.MONTH, within=pyo.NonNegativeReals)

    def min_rule(m, f, t):
        return m.produce[f, t] >= min_production[f] * m.run[f, t]

    def max_rule(m, f, t):
        return m.produce[f, t] <= max_production[f] * m.run[f, t]

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.FACT) >= demand[t]

    model.min_prod = pyo.Constraint(model.FACT, model.MONTH, rule=min_rule)
    model.max_prod = pyo.Constraint(model.FACT, model.MONTH, rule=max_rule)
    model.demand_sat = pyo.Constraint(model.MONTH, rule=demand_rule)

    def obj_rule(m):
        return sum(
            fixed_costs[f] * m.run[f, t] + variable_costs[f] * m.produce[f, t]
            for f in m.FACT
            for t in m.MONTH
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}