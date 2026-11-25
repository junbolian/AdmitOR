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

    factories = list(range(n_factories))
    months = list(range(n_months))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def min_prod_rule(model, f, m):
        return model.prod[f, m] >= min_production[f] * model.run[f, m]

    def max_prod_rule(model, f, m):
        return model.prod[f, m] <= max_production[f] * model.run[f, m]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)
    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(model, m):
        return sum(model.prod[f, m] for f in model.F) >= demand[m]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def obj_rule(model):
        return sum(
            activation_cost[f] * model.run[f, m]
            + production_cost[f] * model.prod[f, m]
            for f in model.F
            for m in model.M
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}