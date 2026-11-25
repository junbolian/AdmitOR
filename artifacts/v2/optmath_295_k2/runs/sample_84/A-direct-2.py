import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    total_time = params["total_time"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit)
    products = list(range(n))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    model.time_con = pyo.Constraint(
        expr=sum(time_per_unit[i] * model.x[i] for i in model.P) <= total_time
    )

    def _lb(model_, i):
        return model.x[i] >= min_production[i]

    def _ub(model_, i):
        return model.x[i] <= max_production[i]

    model.min_con = pyo.Constraint(model.P, rule=_lb)
    model.max_con = pyo.Constraint(model.P, rule=_ub)

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in model.P),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}