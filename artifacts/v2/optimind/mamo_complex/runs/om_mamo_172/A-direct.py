import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "lentils", "apples", "eggs", "broccoli"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.FOODS, within=pyo.NonNegativeReals)

    model.protein = pyo.Param(model.FOODS, initialize={
        f: params["protein_" + f] for f in foods
    })
    model.carbs = pyo.Param(model.FOODS, initialize={
        f: params["carb_" + f] for f in foods
    })
    model.calories = pyo.Param(model.FOODS, initialize={
        f: params["cal_" + f] for f in foods
    })
    model.cost = pyo.Param(model.FOODS, initialize={
        f: params["cost_" + f] for f in foods
    })

    model.protein_con = pyo.Constraint(
        expr=sum(model.protein[f] * model.x[f] for f in model.FOODS)
        >= params["req_protein"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(model.carbs[f] * model.x[f] for f in model.FOODS)
        >= params["req_carbs"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(model.calories[f] * model.x[f] for f in model.FOODS)
        >= params["req_calories"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}