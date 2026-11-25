import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit)
    products = list(range(n))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.P, bounds=lambda m, i: (min_production[i], max_production[i]))

    model.time_con = pyo.Constraint(
        expr=sum(time_per_unit[i] * model.x[i] for i in model.P) <= time_capacity
    )

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in model.P),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}