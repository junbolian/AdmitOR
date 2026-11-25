import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_months = 4
    num_factories = 6
    months = range(num_months)
    factories = range(num_factories)

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.MONTHS = pyo.Set(initialize=list(months))
    model.FACTORIES = pyo.Set(initialize=list(factories))

    model.run = pyo.Var(model.MONTHS, model.FACTORIES, domain=pyo.Binary)
    model.prod = pyo.Var(model.MONTHS, model.FACTORIES, domain=pyo.NonNegativeReals)

    def _min_prod_rule(model, t, f):
        return model.prod[t, f] >= min_production[f] * model.run[t, f]

    def _max_prod_rule(model, t, f):
        return model.prod[t, f] <= max_production[f] * model.run[t, f]

    def _demand_rule(model, t):
        return sum(model.prod[t, f] for f in model.FACTORIES) >= demand[t]

    model.min_prod_con = pyo.Constraint(model.MONTHS, model.FACTORIES, rule=_min_prod_rule)
    model.max_prod_con = pyo.Constraint(model.MONTHS, model.FACTORIES, rule=_max_prod_rule)
    model.demand_con = pyo.Constraint(model.MONTHS, rule=_demand_rule)

    def _obj_rule(model):
        total = 0
        for t in model.MONTHS:
            for f in model.FACTORIES:
                total += fixed_cost[f] * model.run[t, f]
                total += variable_cost[f] * model.prod[t, f]
        return total

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}