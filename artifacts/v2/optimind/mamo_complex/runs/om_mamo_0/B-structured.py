# IR: {"sets":{"foods":[0,1,2,3,4],"food_order":["Steak","Rice","Chicken","Iceberg Lettuce","Almonds"]},"params":{"protein_content":"array[foods]","carb_content":"array[foods]","calorie_content":"array[foods]","cost":"array[foods]","protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar"},"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein_content[i]*portions[i] for i in foods) >= protein_requirement","sum(carb_content[i]*portions[i] for i in foods) >= carb_requirement","sum(calorie_content[i]*portions[i] for i in foods) >= calorie_requirement"],"objective":{"sense":"minimize","expression":"sum(cost[i]*portions[i] for i in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=range(5), ordered=True)

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
    model.cost = pyo.Param(
        model.foods,
        initialize={i: params["cost"][i] for i in model.foods},
    )
    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"]
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"]
    )

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[i] * model.portions[i]
            for i in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[i] * model.portions[i]
            for i in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[i] * model.portions[i]
            for i in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.portions[i] for i in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}