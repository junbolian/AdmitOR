# IR: {"sets":{"foods":[0,1,2,3,4],"food_order":["Chicken","Rice","Beans","Broccoli","Fruit"]},"params":{"protein_content":"foods-indexed array","carb_content":"foods-indexed array","calorie_content":"foods-indexed array","cost":"foods-indexed array","protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar"},"variables":{"quantity[foods]":"continuous, nonnegative"},"constraints":["sum(protein_content[i]*quantity[i] for i in foods) >= protein_requirement","sum(carb_content[i]*quantity[i] for i in foods) >= carb_requirement","sum(calorie_content[i]*quantity[i] for i in foods) >= calorie_requirement"],"objective":"minimize sum(cost[i]*quantity[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 4)

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
        initialize=params["protein_requirement"],
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"],
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"],
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[i] * model.quantity[i]
            for i in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[i] * model.quantity[i]
            for i in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[i] * model.quantity[i]
            for i in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.quantity[i] for i in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}