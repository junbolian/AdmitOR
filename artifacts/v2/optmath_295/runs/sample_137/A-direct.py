import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_time_available = params["stage_time_available"]
    time_per_unit = params["time_per_unit"]
    lower_bound = params["lower_bound"]
    upper_bound = params["upper_bound"]

    n_products = len(profit)
    n_stages = len(stage_time_available)

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, n_products - 1)
    model.stages = pyo.RangeSet(0, n_stages - 1)

    model.production = pyo.Var(model.products, bounds=lambda m, j: (lower_bound[j], upper_bound[j]))

    model.obj = pyo.Objective(
        expr=sum(profit[j] * model.production[j] for j in model.products),
        sense=pyo.maximize,
    )

    model.stage_capacity = pyo.Constraint(
        model.stages,
        rule=lambda m, i: sum(time_per_unit[i][j] * m.production[j] for j in m.products)
        <= stage_time_available[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}