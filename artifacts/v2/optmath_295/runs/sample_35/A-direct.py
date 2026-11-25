import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    resource_consumption_per_unit = params["resource_consumption_per_unit"]
    resource_capacity = params["resource_capacity"]
    production_upper_limits = params["production_upper_limits"]

    n_items = len(profit_per_unit)
    items = list(range(n_items))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, within=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, production_upper_limits[i]))

    model.profit = pyo.Objective(
        expr=sum(profit_per_unit[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.resource = pyo.Constraint(
        expr=sum(resource_consumption_per_unit[i] * model.x[i] for i in items)
        <= resource_capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}