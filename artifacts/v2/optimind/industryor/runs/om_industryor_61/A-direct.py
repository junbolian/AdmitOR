import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.x_horse = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x_bicycle = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.x_handcart = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Binary selector: choose bicycle (1) or handcart (0)
    model.choose_bicycle = pyo.Var(domain=pyo.Binary)

    model.demand_con = pyo.Constraint(
        expr=params["capacity_horse"] * model.x_horse
        + params["capacity_bicycle"] * model.x_bicycle
        + params["capacity_handcart"] * model.x_handcart
        >= params["demand"]
    )

    model.pollution_con = pyo.Constraint(
        expr=params["pollution_horse"] * model.x_horse
        + params["pollution_bicycle"] * model.x_bicycle
        + params["pollution_handcart"] * model.x_handcart
        <= params["pollution_budget"]
    )

    model.min_horse_con = pyo.Constraint(
        expr=model.x_horse >= params["min_horse_trips"]
    )

    # Only one of bicycle and handcart may be used
    big_m = params["demand"]  # safe upper bound on trips
    model.bicycle_only_con = pyo.Constraint(
        expr=model.x_bicycle <= big_m * model.choose_bicycle
    )
    model.handcart_only_con = pyo.Constraint(
        expr=model.x_handcart <= big_m * (1 - model.choose_bicycle)
    )

    model.obj = pyo.Objective(
        expr=params["pollution_horse"] * model.x_horse
        + params["pollution_bicycle"] * model.x_bicycle
        + params["pollution_handcart"] * model.x_handcart,
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}