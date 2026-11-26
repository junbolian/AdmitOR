# IR: {"sets":{"products":[1,2]},"params":["assembly_hours_type1","assembly_hours_type2","testing_hours_type1","testing_hours_type2","raw_material_cost_type1","raw_material_cost_type2","regular_assembly_capacity","testing_capacity","max_overtime_assembly","overtime_cost_per_hour","market_value_type1","market_value_type2"],"variables":{"production[products]":"NonNegativeReals","overtime":"NonNegativeReals"},"constraints":["assembly_hours_type1*production[1]+assembly_hours_type2*production[2]<=regular_assembly_capacity+overtime","testing_hours_type1*production[1]+testing_hours_type2*production[2]<=testing_capacity","overtime<=max_overtime_assembly"],"objective":{"sense":"maximize","expression":"(market_value_type1-raw_material_cost_type1)*production[1]+(market_value_type2-raw_material_cost_type2)*production[2]-overtime_cost_per_hour*overtime"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[1, 2], ordered=True)

    model.assembly_hours_type1 = pyo.Param(
        initialize=params["assembly_hours_type1"]
    )
    model.assembly_hours_type2 = pyo.Param(
        initialize=params["assembly_hours_type2"]
    )
    model.testing_hours_type1 = pyo.Param(
        initialize=params["testing_hours_type1"]
    )
    model.testing_hours_type2 = pyo.Param(
        initialize=params["testing_hours_type2"]
    )
    model.raw_material_cost_type1 = pyo.Param(
        initialize=params["raw_material_cost_type1"]
    )
    model.raw_material_cost_type2 = pyo.Param(
        initialize=params["raw_material_cost_type2"]
    )
    model.regular_assembly_capacity = pyo.Param(
        initialize=params["regular_assembly_capacity"]
    )
    model.testing_capacity = pyo.Param(
        initialize=params["testing_capacity"]
    )
    model.max_overtime_assembly = pyo.Param(
        initialize=params["max_overtime_assembly"]
    )
    model.overtime_cost_per_hour = pyo.Param(
        initialize=params["overtime_cost_per_hour"]
    )
    model.market_value_type1 = pyo.Param(
        initialize=params["market_value_type1"]
    )
    model.market_value_type2 = pyo.Param(
        initialize=params["market_value_type2"]
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    model.assembly_limit = pyo.Constraint(
        expr=(
            model.assembly_hours_type1 * model.production[1]
            + model.assembly_hours_type2 * model.production[2]
            <= model.regular_assembly_capacity + model.overtime
        )
    )
    model.testing_limit = pyo.Constraint(
        expr=(
            model.testing_hours_type1 * model.production[1]
            + model.testing_hours_type2 * model.production[2]
            <= model.testing_capacity
        )
    )
    model.overtime_limit = pyo.Constraint(
        expr=model.overtime <= model.max_overtime_assembly
    )

    model.daily_profit = pyo.Objective(
        expr=(
            (model.market_value_type1 - model.raw_material_cost_type1)
            * model.production[1]
            + (model.market_value_type2 - model.raw_material_cost_type2)
            * model.production[2]
            - model.overtime_cost_per_hour * model.overtime
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.daily_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}