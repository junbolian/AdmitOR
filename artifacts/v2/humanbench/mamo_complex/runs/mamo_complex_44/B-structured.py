# IR: {"sets":{"products":[1,2]},"params":["assembly_hours_type1","testing_hours_type1","materials_cost_type1","assembly_hours_type2","testing_hours_type2","materials_cost_type2","regular_assembly_capacity","testing_capacity","overtime_assembly_capacity","overtime_cost_per_hour","market_value_type1","market_value_type2"],"variables":{"quantity[products]":"NonNegativeReals","overtime_hours":"NonNegativeReals"},"constraints":["assembly_hours_type1*quantity[1]+assembly_hours_type2*quantity[2] <= regular_assembly_capacity+overtime_hours","testing_hours_type1*quantity[1]+testing_hours_type2*quantity[2] <= testing_capacity","overtime_hours <= overtime_assembly_capacity"],"objective":{"sense":"maximize","expression":"(market_value_type1-materials_cost_type1)*quantity[1]+(market_value_type2-materials_cost_type2)*quantity[2]-overtime_cost_per_hour*overtime_hours"},"output":{"objective":"optimal profit rounded to the nearest dollar"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    parameter_values = {
        "assembly_hours_type1": params["assembly_hours_type1"],
        "testing_hours_type1": params["testing_hours_type1"],
        "materials_cost_type1": params["materials_cost_type1"],
        "assembly_hours_type2": params["assembly_hours_type2"],
        "testing_hours_type2": params["testing_hours_type2"],
        "materials_cost_type2": params["materials_cost_type2"],
        "regular_assembly_capacity": params["regular_assembly_capacity"],
        "testing_capacity": params["testing_capacity"],
        "overtime_assembly_capacity": params["overtime_assembly_capacity"],
        "overtime_cost_per_hour": params["overtime_cost_per_hour"],
        "market_value_type1": params["market_value_type1"],
        "market_value_type2": params["market_value_type2"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=[1, 2], ordered=True)
    model.inputs = pyo.Param(
        list(parameter_values),
        initialize=parameter_values,
        within=pyo.NonNegativeReals,
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.overtime_hours = pyo.Var(domain=pyo.NonNegativeReals)

    model.assembly_limit = pyo.Constraint(
        expr=(
            model.inputs["assembly_hours_type1"] * model.quantity[1]
            + model.inputs["assembly_hours_type2"] * model.quantity[2]
            <= model.inputs["regular_assembly_capacity"] + model.overtime_hours
        )
    )

    model.testing_limit = pyo.Constraint(
        expr=(
            model.inputs["testing_hours_type1"] * model.quantity[1]
            + model.inputs["testing_hours_type2"] * model.quantity[2]
            <= model.inputs["testing_capacity"]
        )
    )

    model.overtime_limit = pyo.Constraint(
        expr=(
            model.overtime_hours
            <= model.inputs["overtime_assembly_capacity"]
        )
    )

    model.daily_profit = pyo.Objective(
        expr=(
            (
                model.inputs["market_value_type1"]
                - model.inputs["materials_cost_type1"]
            )
            * model.quantity[1]
            + (
                model.inputs["market_value_type2"]
                - model.inputs["materials_cost_type2"]
            )
            * model.quantity[2]
            - model.inputs["overtime_cost_per_hour"] * model.overtime_hours
        ),
        sense=pyo.maximize,
    )

    # HiGHS can raise when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    # Objective retrieval is the sole success check.
    try:
        obj_val = float(pyo.value(model.daily_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}