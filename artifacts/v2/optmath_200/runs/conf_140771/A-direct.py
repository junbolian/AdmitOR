import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_factories = 4
    num_months = 5
    factories = range(num_factories)
    months = range(num_months)

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    model.fixed_cost_expr = pyo.Expression(
        expr=sum(fixed_cost[i] * model.run[i, j] for i in model.F for j in model.M)
    )
    model.variable_cost_expr = pyo.Expression(
        expr=sum(variable_cost[i] * model.prod[i, j] for i in model.F for j in model.M)
    )

    model.total_cost = pyo.Objective(
        expr=model.fixed_cost_expr + model.variable_cost_expr,
        sense=pyo.minimize,
    )

    def min_prod_rule(m, i, j):
        return m.prod[i, j] >= min_production[i] * m.run[i, j]

    model.min_prod_con = pyo.Constraint(model.F, model.M, rule=min_prod_rule)

    def max_prod_rule(m, i, j):
        return m.prod[i, j] <= max_production[i] * m.run[i, j]

    model.max_prod_con = pyo.Constraint(model.F, model.M, rule=max_prod_rule)

    def demand_rule(m, j):
        return sum(m.prod[i, j] for i in m.F) >= demand[j]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}