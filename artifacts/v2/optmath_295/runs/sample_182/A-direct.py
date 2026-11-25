import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    factories = list(range(6))
    months = list(range(4))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, within=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, within=pyo.NonNegativeReals)

    model.obj_expr = pyo.Objective(
        expr=pyo.quicksum(
            fixed_cost[f] * model.run[f, t] + variable_cost[f] * model.prod[f, t]
            for f in model.F
            for t in model.M
        ),
        sense=pyo.minimize,
    )

    def min_prod_rule(mdl, f, t):
        return mdl.prod[f, t] >= min_production[f] * mdl.run[f, t]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(mdl, f, t):
        return mdl.prod[f, t] <= max_production[f] * mdl.run[f, t]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(mdl, t):
        return pyo.quicksum(mdl.prod[f, t] for f in mdl.F) >= demand[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj_expr))
    return {"objective": obj_val, "status": "optimal"}