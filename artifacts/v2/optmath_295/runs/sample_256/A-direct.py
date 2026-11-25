import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 4
    num_months = 4
    factories = range(num_factories)
    months = range(num_months)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            activation_cost[fac] * m.run[fac, mon]
            + production_cost[fac] * m.produce[fac, mon]
            for fac in m.F
            for mon in m.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, fac, mon):
        return m.produce[fac, mon] >= min_production[fac] * m.run[fac, mon]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(m, fac, mon):
        return m.produce[fac, mon] <= max_production[fac] * m.run[fac, mon]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(m, mon):
        return sum(m.produce[fac, mon] for fac in m.F) >= demand[mon]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}