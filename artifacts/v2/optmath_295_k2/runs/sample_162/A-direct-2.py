import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    factories = list(range(6))
    months = list(range(4))

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.M, model.F, within=pyo.Binary)
    model.prod = pyo.Var(model.M, model.F, within=pyo.NonNegativeReals)

    def fixed_cost(m, j, f):
        return params[f"fixed_cost_f{f}_month{j}"]

    def var_cost(m, f):
        return params[f"var_cost_f{f}"]

    def min_prod(f):
        return params[f"min_prod_f{f}"]

    def max_prod(f):
        return params[f"max_prod_f{f}"]

    def demand(j):
        return params[f"demand_month{j}"]

    model.obj = pyo.Objective(
        expr=sum(fixed_cost(model, j, f) * model.run[j, f] for j in months for f in factories)
             + sum(var_cost(model, f) * model.prod[j, f] for j in months for f in factories),
        sense=pyo.minimize,
    )

    # Min production bounds
    model.min_rule = pyo.Constraint(
        model.M, model.F,
        rule=lambda m, j, f: m.prod[j, f] >= min_prod(f) * m.run[j, f],
    )

    # Max production bounds
    model.max_rule = pyo.Constraint(
        model.M, model.F,
        rule=lambda m, j, f: m.prod[j, f] <= max_prod(f) * m.run[j, f],
    )

    # Demand satisfaction
    model.demand_rule = pyo.Constraint(
        model.M,
        rule=lambda m, j: sum(m.prod[j, f] for f in m.F) >= demand(j),
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}