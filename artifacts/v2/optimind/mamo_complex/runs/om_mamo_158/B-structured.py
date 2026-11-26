# IR: {"sets":{"foods":["chicken","rice","veg","bread","almonds","salmon"]},"params":{"protein":["protein_chicken","protein_rice","protein_veg","protein_bread","protein_almonds","protein_salmon"],"carb":["carb_chicken","carb_rice","carb_veg","carb_bread","carb_almonds","carb_salmon"],"cal":["cal_chicken","cal_rice","cal_veg","cal_bread","cal_almonds","cal_salmon"],"cost":["cost_chicken","cost_rice","cost_veg","cost_bread","cost_almonds","cost_salmon"],"targets":["protein_target","carb_target","cal_target"]},"variables":{"portions[food]":"nonnegative integer"},"constraints":["sum(protein[food]*portions[food]) >= protein_target","sum(carb[food]*portions[food]) >= carb_target","sum(cal[food]*portions[food]) >= cal_target"],"objective":"minimize sum(cost[food]*portions[food])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ("chicken", "rice", "veg", "bread", "almonds", "salmon")

    food_data = {
        "chicken": (
            params["protein_chicken"],
            params["carb_chicken"],
            params["cal_chicken"],
            params["cost_chicken"],
        ),
        "rice": (
            params["protein_rice"],
            params["carb_rice"],
            params["cal_rice"],
            params["cost_rice"],
        ),
        "veg": (
            params["protein_veg"],
            params["carb_veg"],
            params["cal_veg"],
            params["cost_veg"],
        ),
        "bread": (
            params["protein_bread"],
            params["carb_bread"],
            params["cal_bread"],
            params["cost_bread"],
        ),
        "almonds": (
            params["protein_almonds"],
            params["carb_almonds"],
            params["cal_almonds"],
            params["cost_almonds"],
        ),
        "salmon": (
            params["protein_salmon"],
            params["carb_salmon"],
            params["cal_salmon"],
            params["cost_salmon"],
        ),
    }

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein = pyo.Param(
        model.foods,
        initialize={food: food_data[food][0] for food in foods},
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={food: food_data[food][1] for food in foods},
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={food: food_data[food][2] for food in foods},
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={food: food_data[food][3] for food in foods},
    )

    model.protein_target = pyo.Param(initialize=params["protein_target"])
    model.carb_target = pyo.Param(initialize=params["carb_target"])
    model.cal_target = pyo.Param(initialize=params["cal_target"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_target
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.portions[food]
            for food in model.foods
        ) >= model.carb_target
    )
    model.cal_requirement = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.portions[food]
            for food in model.foods
        ) >= model.cal_target
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}