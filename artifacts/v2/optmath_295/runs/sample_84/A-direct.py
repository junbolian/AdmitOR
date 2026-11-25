import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    time_per_unit = params["time_per_unit"]
    total_time_available = params["total_time_available"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit_per_unit)

    model = pyo.ConcreteModel()
    model.PRODUCTS = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.PRODUCTS, within=pyo.NonNegativeReals,
                      bounds=lambda m, i: (min_production[i], max_production[i]))

    model.profit = pyo.Objective(
        expr=sum(profit_per_unit[i] * model.x[i] for i in model.PRODUCTS),
        sense=pyo.maximize,
    )

    model.time_limit = pyo.Constraint(
        expr=sum(time_per_unit[i] * model.x[i] for i in model.PRODUCTS)
        <= total_time_available
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}