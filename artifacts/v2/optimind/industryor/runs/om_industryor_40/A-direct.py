import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    m = params["m"]
    n = params["n"]
    k = params["k"]
    d = params["d"]
    c = params["c"]

    model = pyo.ConcreteModel()

    model.METHODS = pyo.Set(initialize=[1, 2])

    # x[1], x[2] = number of furnaces assigned each method
    model.x = pyo.Var(model.METHODS, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=m * model.x[1] + n * model.x[2],
        sense=pyo.minimize,
    )

    # Total hours constraint
    model.hours = pyo.Constraint(
        expr=a * model.x[1] + b * model.x[2] <= c
    )

    # Minimum steel production constraint
    model.steel = pyo.Constraint(
        expr=k * (model.x[1] + model.x[2]) >= d
    )

    # At most 2 furnaces total (two furnaces, each using one method)
    model.furnaces = pyo.Constraint(
        expr=model.x[1] + model.x[2] <= 2
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}