import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_prod = params["min_prod"]
    max_prod = params["max_prod"]

    n = len(profit)
    products = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in products),
        sense=pyo.maximize,
    )

    model.time_cap = pyo.Constraint(
        expr=sum(time_per_unit[i] * model.x[i] for i in products) <= time_capacity
    )

    model.min_req = pyo.Constraint(
        products,
        rule=lambda m, i: m.x[i] >= min_prod[i],
    )

    model.max_req = pyo.Constraint(
        products,
        rule=lambda m, i: m.x[i] <= max_prod[i],
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.profit_expr))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as e:
        return {"objective": None, "status": str(e)}