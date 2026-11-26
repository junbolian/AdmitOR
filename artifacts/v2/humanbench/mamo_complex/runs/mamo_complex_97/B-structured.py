# IR: {"sets":{"foods":"0..7: chicken breast, tofu, spinach, beef steak, eggs, brown rice, bananas, quinoa"},"params":{"protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar","cost":"array[8]","protein_content":"array[8]","carb_content":"array[8]","calorie_content":"array[8]"},"variables":{"servings[foods]":"continuous, nonnegative"},"constraints":["sum(protein_content[i]*servings[i]) >= protein_requirement","sum(carb_content[i]*servings[i]) >= carb_requirement","sum(calorie_content[i]*servings[i]) >= calorie_requirement"],"objective":"minimize sum(cost[i]*servings[i])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 7)

    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"]
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"]
    )

    model.cost = pyo.Param(
        model.foods,
        initialize={i: params["cost"][i] for i in model.foods},
    )
    model.protein_content = pyo.Param(
        model.foods,
        initialize={i: params["protein_content"][i] for i in model.foods},
    )
    model.carb_content = pyo.Param(
        model.foods,
        initialize={i: params["carb_content"][i] for i in model.foods},
    )
    model.calorie_content = pyo.Param(
        model.foods,
        initialize={i: params["calorie_content"][i] for i in model.foods},
    )

    model.servings = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[i] * model.servings[i]
            for i in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[i] * model.servings[i]
            for i in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[i] * model.servings[i]
            for i in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.servings[i] for i in model.foods),
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