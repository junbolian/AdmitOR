import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_factories = int(params["num_factories"])
    num_months = int(params["num_months"])

    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, num_factories - 1)
    model.M = pyo.RangeSet(0, num_months - 1)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def min_prod_rule(mdl, i, t):
        return mdl.produce[i, t] >= min_production[i] * mdl.run[i, t]

    def max_prod_rule(mdl, i, t):
        return mdl.produce[i, t] <= max_production[i] * mdl.run[i, t]

    model.min_prod = pyo.Constraint(model.F, model.M, rule=min_prod_rule)
    model.max_prod = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(mdl, t):
        return sum(mdl.produce[i, t] for i in mdl.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def obj_rule(mdl):
        return sum(
            activation_cost[i] * mdl.run[i, t] + production_cost[i] * mdl.produce[i, t]
            for i in mdl.F
            for t in mdl.M
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}