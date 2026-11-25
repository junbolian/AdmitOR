import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_hours = params["stage_hours"]
    time_coeff = params["time_coeff"]
    min_commitment = params["min_commitment"]
    demand_limit = params["demand_limit"]

    n_products = len(profit)
    n_stages = len(stage_hours)

    products = range(n_products)
    stages = range(n_stages)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, bounds=lambda m, j: (min_commitment[j], demand_limit[j]))

    model.profit_expr = pyo.Expression(rule=lambda m: sum(profit[j] * m.x[j] for j in products))

    model.stage_con = pyo.Constraint(
        stages,
        rule=lambda m, i: sum(time_coeff[i * n_products + j] * m.x[j] for j in products) <= stage_hours[i]
    )

    model.obj = pyo.Objective(rule=lambda m: m.profit_expr, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}