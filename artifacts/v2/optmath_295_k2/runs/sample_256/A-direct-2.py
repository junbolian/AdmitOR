import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    factories = list(range(4))
    months = list(range(4))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def min_prod_rule(m, f, t):
        return m.prod[f, t] >= min_production[f] * m.run[f, t]

    def max_prod_rule(m, f, t):
        return m.prod[f, t] <= max_production[f] * m.run[f, t]

    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= demand[t]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)
    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def obj_rule(m):
        return sum(
            activation_cost[f] * m.run[f, t] + production_cost[f] * m.prod[f, t]
            for f in m.F for t in m.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}