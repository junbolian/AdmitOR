import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    consumption = params["resource_consumption"]
    capacity = params["resource_capacity"]
    max_prod = params["max_production"]

    items = list(range(15))

    model = pyo.ConcreteModel()

    model.Items = pyo.Set(initialize=items)

    model.x = pyo.Var(model.Items, domain=pyo.NonNegativeReals)

    profit_coeffs = {i: profit[i] for i in items}
    model.profit_expr = pyo.Expression(
        expr=sum(profit_coeffs[i] * model.x[i] for i in model.Items)
    )

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    cons_coeffs = {i: consumption[i] for i in items}
    model.resource_con = pyo.Constraint(
        expr=sum(cons_coeffs[i] * model.x[i] for i in model.Items) <= capacity
    )

    upper = {i: max_prod[i] for i in items}
    model.prod_con = pyo.Constraint(
        model.Items, rule=lambda model, i: model.x[i] <= upper[i]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}