# IR: {"sets":{"foods":[1,2,3,4]},"params":["cost_food1","cost_food2","cost_food3","cost_food4","protein_food1","protein_food2","protein_food3","protein_food4","carb_food1","carb_food2","carb_food3","carb_food4","calories_food1","calories_food2","calories_food3","calories_food4","protein_req","carb_req","calorie_req"],"variables":{"quantity[i]":{"type":"continuous","lower_bound":0,"index":"foods"}},"constraints":["sum(protein_food[i]*quantity[i] for i in foods) >= protein_req","sum(carb_food[i]*quantity[i] for i in foods) >= carb_req","sum(calories_food[i]*quantity[i] for i in foods) >= calorie_req"],"objective":{"sense":"minimize","expression":"sum(cost_food[i]*quantity[i] for i in foods)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=[1, 2, 3, 4], ordered=True)

    model.cost_food = pyo.Param(
        model.foods,
        initialize={
            1: params["cost_food1"],
            2: params["cost_food2"],
            3: params["cost_food3"],
            4: params["cost_food4"],
        },
    )
    model.protein_food = pyo.Param(
        model.foods,
        initialize={
            1: params["protein_food1"],
            2: params["protein_food2"],
            3: params["protein_food3"],
            4: params["protein_food4"],
        },
    )
    model.carb_food = pyo.Param(
        model.foods,
        initialize={
            1: params["carb_food1"],
            2: params["carb_food2"],
            3: params["carb_food3"],
            4: params["carb_food4"],
        },
    )
    model.calories_food = pyo.Param(
        model.foods,
        initialize={
            1: params["calories_food1"],
            2: params["calories_food2"],
            3: params["calories_food3"],
            4: params["calories_food4"],
        },
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_food[i] * model.quantity[i] for i in model.foods
        ) >= model.protein_req
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_food[i] * model.quantity[i] for i in model.foods
        ) >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories_food[i] * model.quantity[i] for i in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost_food[i] * model.quantity[i] for i in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}