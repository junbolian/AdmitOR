# IR: {"sets":{"methods":[1,2]},"params":["a","b","m","n","k","d","c"],"variables":{"x[j]":{"type":"NonNegativeReals","meaning":"furnace-equivalent production runs using method j, aggregated across both furnaces"}},"constraints":["a*x[1] + b*x[2] <= c (total available furnace-hours)","k*(x[1] + x[2]) >= d"],"objective":{"sense":"minimize","expression":"m*x[1] + n*x[2]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Continuous production quantities implement the requested LP.
    # The parameter c is the total shared furnace-hour budget.
    a = params["a"]
    b = params["b"]
    fuel_cost_1 = params["m"]
    fuel_cost_2 = params["n"]
    k = params["k"]
    d = params["d"]
    c = params["c"]

    model = pyo.ConcreteModel()
    model.methods = pyo.Set(initialize=[1, 2])
    model.x = pyo.Var(model.methods, domain=pyo.NonNegativeReals)

    model.hours_limit = pyo.Constraint(
        expr=a * model.x[1] + b * model.x[2] <= c
    )
    model.production_requirement = pyo.Constraint(
        expr=k * (model.x[1] + model.x[2]) >= d
    )
    model.total_fuel_cost = pyo.Objective(
        expr=fuel_cost_1 * model.x[1] + fuel_cost_2 * model.x[2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Includes failure to load a solution when the LP is infeasible.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_fuel_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}