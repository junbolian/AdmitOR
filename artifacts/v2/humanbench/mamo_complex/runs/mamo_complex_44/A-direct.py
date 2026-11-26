import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.ot = pyo.Var(domain=pyo.NonNegativeReals)

    model.assembly = pyo.Constraint(
        expr=params["assembly_hours_type1"] * model.x1
        + params["assembly_hours_type2"] * model.x2
        <= params["regular_assembly_capacity"]
    )
    model.testing = pyo.Constraint(
        expr=params["testing_hours_type1"] * model.x1
        + params["testing_hours_type2"] * model.x2
        <= params["testing_capacity"]
    )
    model.overtime = pyo.Constraint(
        expr=model.ot <= params["overtime_assembly_capacity"]
    )

    model.obj = pyo.Objective(
        expr=params["market_value_type1"] * model.x1
        + params["market_value_type2"] * model.x2
        - params["materials_cost_type1"] * model.x1
        - params["materials_cost_type2"] * model.x2
        - params["overtime_cost_per_hour"] * model.ot,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}