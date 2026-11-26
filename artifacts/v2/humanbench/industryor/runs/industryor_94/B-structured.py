# IR: {"sets":{"methods":[1,2]},"params":["a","b","m","n","k","d","c"],"input_validation":{"missing_required_parameter":"return objective=null,status=missing_params"},"variables":{"x[i]":{"index":"methods","type":"nonnegative continuous","meaning":"furnace-equivalent runs using method i"}},"constraints":["k*(x[1]+x[2]) >= d","a*x[1]+b*x[2] <= c"],"objective":{"sense":"minimize","expression":"m*x[1]+n*x[2]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_keys = ("a", "b", "m", "n", "k", "d", "c")
    if any(key not in params for key in required_keys):
        return {"objective": None, "status": "missing_params"}

    model = pyo.ConcreteModel()
    model.methods = pyo.Set(initialize=[1, 2], ordered=True)

    model.a = pyo.Param(initialize=params["a"])
    model.b = pyo.Param(initialize=params["b"])
    model.m = pyo.Param(initialize=params["m"])
    model.n = pyo.Param(initialize=params["n"])
    model.k = pyo.Param(initialize=params["k"])
    model.d = pyo.Param(initialize=params["d"])
    model.c = pyo.Param(initialize=params["c"])

    model.x = pyo.Var(model.methods, domain=pyo.NonNegativeReals)

    model.production_requirement = pyo.Constraint(
        expr=model.k * (model.x[1] + model.x[2]) >= model.d
    )
    model.available_hours = pyo.Constraint(
        expr=model.a * model.x[1] + model.b * model.x[2] <= model.c
    )
    model.total_fuel_cost = pyo.Objective(
        expr=model.m * model.x[1] + model.n * model.x[2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_fuel_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}