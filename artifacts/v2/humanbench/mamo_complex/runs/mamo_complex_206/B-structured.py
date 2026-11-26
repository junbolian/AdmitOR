# IR: {"sets":{"grains":[1,2,3],"nutrients":["A","B","C","D"]},"params":{"nutrient_units":{"A":["nutrient_A_grain1","nutrient_A_grain2","nutrient_A_grain3"],"B":["nutrient_B_grain1","nutrient_B_grain2","nutrient_B_grain3"],"C":["nutrient_C_grain1","nutrient_C_grain2","nutrient_C_grain3"],"D":["nutrient_D_grain1","nutrient_D_grain2","nutrient_D_grain3"]},"cost_cents":["cost_grain1","cost_grain2","cost_grain3"],"minimum_units":["req_nutrient_A","req_nutrient_B","req_nutrient_C","req_nutrient_D"]},"variables":{"grain_pounds[g]":{"type":"continuous","domain":"nonnegative","units":"pounds per sheep per day"}},"constraints":["For each nutrient n: sum(nutrient_units[n,g]*grain_pounds[g] for g in grains) >= minimum_units[n]"],"objective":{"sense":"minimize","expression":"sum(cost_cents[g]*grain_pounds[g] for g in grains)","units":"cents per sheep per day"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.grains = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.nutrients = pyo.Set(initialize=["A", "B", "C", "D"], ordered=True)

    model.nutrient_units = pyo.Param(
        model.nutrients,
        model.grains,
        initialize={
            ("A", 1): params["nutrient_A_grain1"],
            ("B", 1): params["nutrient_B_grain1"],
            ("C", 1): params["nutrient_C_grain1"],
            ("D", 1): params["nutrient_D_grain1"],
            ("A", 2): params["nutrient_A_grain2"],
            ("B", 2): params["nutrient_B_grain2"],
            ("C", 2): params["nutrient_C_grain2"],
            ("D", 2): params["nutrient_D_grain2"],
            ("A", 3): params["nutrient_A_grain3"],
            ("B", 3): params["nutrient_B_grain3"],
            ("C", 3): params["nutrient_C_grain3"],
            ("D", 3): params["nutrient_D_grain3"],
        },
        within=pyo.Reals,
    )

    model.cost_cents = pyo.Param(
        model.grains,
        initialize={
            1: params["cost_grain1"],
            2: params["cost_grain2"],
            3: params["cost_grain3"],
        },
        within=pyo.Reals,
    )

    model.minimum_units = pyo.Param(
        model.nutrients,
        initialize={
            "A": params["req_nutrient_A"],
            "B": params["req_nutrient_B"],
            "C": params["req_nutrient_C"],
            "D": params["req_nutrient_D"],
        },
        within=pyo.Reals,
    )

    model.grain_pounds = pyo.Var(
        model.grains,
        domain=pyo.NonNegativeReals,
    )

    def nutrient_requirement_rule(instance, nutrient):
        return (
            sum(
                instance.nutrient_units[nutrient, grain]
                * instance.grain_pounds[grain]
                for grain in instance.grains
            )
            >= instance.minimum_units[nutrient]
        )

    model.nutrient_requirements = pyo.Constraint(
        model.nutrients,
        rule=nutrient_requirement_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_cents[grain] * model.grain_pounds[grain]
            for grain in model.grains
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}