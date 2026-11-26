# IR: {"sets":{"F":[0,1,2,3,4,5],"food_order":["chicken breast","brown rice","tofu","spinach","almonds","salmon"]},"params":{"costs":"real[F], from params","protein_content":"real[F], from params","carb_content":"real[F], from params","calorie_content":"real[F], from params","protein_requirement":"real, from params","carb_requirement":"real, from params","calorie_requirement":"real, from params"},"variables":{"servings[f]":"continuous nonnegative, f in F"},"constraints":["sum(protein_content[f]*servings[f] for f in F) >= protein_requirement","sum(carb_content[f]*servings[f] for f in F) >= carb_requirement","sum(calorie_content[f]*servings[f] for f in F) >= calorie_requirement"],"objective":"minimize sum(costs[f]*servings[f] for f in F)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Nutrient and cost inputs are sequences indexed in the IR food order."""
    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, 5)

    model.costs = pyo.Param(
        model.F,
        initialize={food_idx: params["costs"][food_idx] for food_idx in model.F},
        within=pyo.Reals,
    )
    model.protein_content = pyo.Param(
        model.F,
        initialize={
            food_idx: params["protein_content"][food_idx]
            for food_idx in model.F
        },
        within=pyo.Reals,
    )
    model.carb_content = pyo.Param(
        model.F,
        initialize={
            food_idx: params["carb_content"][food_idx]
            for food_idx in model.F
        },
        within=pyo.Reals,
    )
    model.calorie_content = pyo.Param(
        model.F,
        initialize={
            food_idx: params["calorie_content"][food_idx]
            for food_idx in model.F
        },
        within=pyo.Reals,
    )
    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"], within=pyo.Reals
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"], within=pyo.Reals
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"], within=pyo.Reals
    )

    model.servings = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[food_idx] * model.servings[food_idx]
            for food_idx in model.F
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[food_idx] * model.servings[food_idx]
            for food_idx in model.F
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[food_idx] * model.servings[food_idx]
            for food_idx in model.F
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[food_idx] * model.servings[food_idx]
            for food_idx in model.F
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no solution is available to load.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}