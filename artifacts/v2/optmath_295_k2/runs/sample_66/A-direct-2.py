import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    F = int(params["num_factories"])
    T = int(params["num_months"])

    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, F - 1)
    model.T = pyo.RangeSet(0, T - 1)

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            activation_cost[f] * m.run[f, t] + production_cost[f] * m.prod[f, t]
            for f in m.F
            for t in m.T
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, f, t):
        return m.prod[f, t] >= min_production[f] * m.run[f, t]

    model.min_prod_con = pyo.Constraint(model.F, model.T, rule=min_prod_rule)

    def max_prod_rule(m, f, t):
        return m.prod[f, t] <= max_production[f] * m.run[f, t]

    model.max_prod_con = pyo.Constraint(model.F, model.T, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}