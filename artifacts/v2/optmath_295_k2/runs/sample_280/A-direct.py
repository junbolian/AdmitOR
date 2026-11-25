import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_factories = len(activation_cost)
    n_months = len(demand)

    model = pyo.ConcreteModel()

    model.FACTORIES = pyo.RangeSet(0, n_factories - 1)
    model.MONTHS = pyo.RangeSet(0, n_months - 1)

    model.run_flag = pyo.Var(model.FACTORIES, model.MONTHS, domain=pyo.Binary)
    model.produce = pyo.Var(model.FACTORIES, model.MONTHS, domain=pyo.NonNegativeReals)

    def min_prod_rule(m, f, t):
        return m.produce[f, t] >= min_production[f] * m.run_flag[f, t]

    model.min_prod_con = pyo.Constraint(model.FACTORIES, model.MONTHS, rule=min_prod_rule)

    def max_prod_rule(m, f, t):
        return m.produce[f, t] <= max_production[f] * m.run_flag[f, t]

    model.max_prod_con = pyo.Constraint(model.FACTORIES, model.MONTHS, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.FACTORIES) >= demand[t]

    model.demand_con = pyo.Constraint(model.MONTHS, rule=demand_rule)

    def total_cost_rule(m):
        return sum(
            activation_cost[f] * m.run_flag[f, t] + production_cost[f] * m.produce[f, t]
            for f in m.FACTORIES
            for t in m.MONTHS
        )

    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}