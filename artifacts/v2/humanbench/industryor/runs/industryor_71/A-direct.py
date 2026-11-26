import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.T = pyo.Var(domain=pyo.NonNegativeReals)
    model.P = pyo.Var(domain=pyo.NonNegativeReals)
    model.B = pyo.Var(domain=pyo.NonNegativeReals)
    model.R = pyo.Var(domain=pyo.NonNegativeReals)

    # Binary indicators for logical constraints
    model.zT = pyo.Var(domain=pyo.Binary)
    model.zB = pyo.Var(domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=params["profit_truck"] * model.T
        + params["profit_plane"] * model.P
        + params["profit_boat"] * model.B
        + params["profit_train"] * model.R,
        sense=pyo.maximize,
    )

    model.wood = pyo.Constraint(
        expr=params["wood_truck"] * model.T
        + params["wood_plane"] * model.P
        + params["wood_boat"] * model.B
        + params["wood_train"] * model.R
        <= params["wood_available"]
    )

    model.steel = pyo.Constraint(
        expr=params["steel_truck"] * model.T
        + params["steel_plane"] * model.P
        + params["steel_boat"] * model.B
        + params["steel_train"] * model.R
        <= params["steel_available"]
    )

    # Truck and train are mutually exclusive: if trucks made, no trains.
    model.logic_truck_train = pyo.Constraint(
        expr=model.T <= params["wood_available"] * (1 - model.zT)
    )
    model.logic_train_lim = pyo.Constraint(
        expr=model.R <= params["wood_available"] * model.zT
    )

    # If boats made, planes must be made.
    model.logic_boat_plane = pyo.Constraint(
        expr=model.B <= params["wood_available"] * model.zB
    )
    model.logic_plane_lim = pyo.Constraint(
        expr=model.P >= model.zB
    )

    # Boats cannot exceed trains.
    model.boat_train = pyo.Constraint(expr=model.B <= model.R)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}