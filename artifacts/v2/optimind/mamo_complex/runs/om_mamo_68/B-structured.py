# IR: {"sets":{"foods":["chicken","rice","tuna","beef","corn","whey"]},"params":["protein_chicken","carb_chicken","cal_chicken","cost_chicken","protein_rice","carb_rice","cal_rice","cost_rice","protein_tuna","carb_tuna","cal_tuna","cost_tuna","protein_beef","carb_beef","cal_beef","cost_beef","protein_corn","carb_corn","cal_corn","cost_corn","protein_whey","carb_whey","cal_whey","cost_whey","protein_target","carb_target","cal_target"],"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein[f]*portions[f] for f in foods) >= protein_target","sum(carb[f]*portions[f] for f in foods) >= carb_target","sum(cal[f]*portions[f] for f in foods) >= cal_target"],"objective":"minimize sum(cost[f]*portions[f] for f in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["chicken", "rice", "tuna", "beef", "corn", "whey"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["protein_chicken"],
            "rice": params["protein_rice"],
            "tuna": params["protein_tuna"],
            "beef": params["protein_beef"],
            "corn": params["protein_corn"],
            "whey": params["protein_whey"],
        },
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["carb_chicken"],
            "rice": params["carb_rice"],
            "tuna": params["carb_tuna"],
            "beef": params["carb_beef"],
            "corn": params["carb_corn"],
            "whey": params["carb_whey"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cal_chicken"],
            "rice": params["cal_rice"],
            "tuna": params["cal_tuna"],
            "beef": params["cal_beef"],
            "corn": params["cal_corn"],
            "whey": params["cal_whey"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "chicken": params["cost_chicken"],
            "rice": params["cost_rice"],
            "tuna": params["cost_tuna"],
            "beef": params["cost_beef"],
            "corn": params["cost_corn"],
            "whey": params["cost_whey"],
        },
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