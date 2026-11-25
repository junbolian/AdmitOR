import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    consumption = params["resource_consumption_per_unit"]
    capacity = params["resource_capacity"]
    upper = params["production_upper_bounds"]

    n = len(profit)
    item_ids = list(range(n))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_ids)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Expression(
        expr=sum(profit[i] * model.x[i] for i in model.item_set)
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(consumption[i] * model.x[i] for i in model.item_set) <= capacity
    )

    model.upper_bounds = pyo.Constraint(
        model.item_set, rule=lambda m, i: m.x[i] <= upper[i]
    )

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}