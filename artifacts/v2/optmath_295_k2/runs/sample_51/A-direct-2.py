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
    factories = range(num_factories)
    months = range(num_months)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.produce = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    def production_lb_rule(model, f, m):
        return model.produce[f, m] >= min_production[f] * model.run[f, m]

    def production_ub_rule(model, f, m):
        return model.produce[f, m] <= max_production[f] * model.run[f, m]

    model.production_lb = pyo.Constraint(model.F, model.M, rule=production_lb_rule)
    model.production_ub = pyo.Constraint(model.F, model.M, rule=production_ub_rule)

    def demand_rule(model, m):
        return sum(model.produce[f, m] for f in model.F) >= demand[m]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    def total_cost_rule(model):
        fixed = sum(fixed_cost[f] * model.run[f, m] for f in model.F for m in model.M)
        variable = sum(variable_cost[f] * model.produce[f, m] for f in model.F for m in model.M)
        return fixed + variable

    model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}