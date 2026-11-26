# IR: {"sets":{"foods":[0,1,2,3,4,5]},"params":{"cost":"cost[i] from params","protein":"protein[i] from params","carbs":"carbs[i] from params","calories":"calories[i] from params","protein_req":"scalar from params","carbs_req":"scalar from params","calories_req":"scalar from params"},"variables":{"quantity[i]":"continuous, nonnegative"},"constraints":["sum(protein[i]*quantity[i] for i in foods) >= protein_req","sum(carbs[i]*quantity[i] for i in foods) >= carbs_req","sum(calories[i]*quantity[i] for i in foods) >= calories_req"],"objective":"minimize sum(cost[i]*quantity[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the continuous six-food minimum-cost diet problem.

    Indexed inputs cost, protein, carbs, and calories must be sequences
    of six numbers, ordered Food_1 through Food_6, or mappings keyed 0..5.
    Requirement inputs must be numeric scalars.
    """
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=range(6), ordered=True)

    model.cost = pyo.Param(
        model.foods,
        initialize={idx: params["cost"][idx] for idx in range(6)},
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={idx: params["protein"][idx] for idx in range(6)},
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={idx: params["carbs"][idx] for idx in range(6)},
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={idx: params["calories"][idx] for idx in range(6)},
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carbs_req = pyo.Param(initialize=params["carbs_req"])
    model.calories_req = pyo.Param(initialize=params["calories_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein[idx] * model.quantity[idx] for idx in model.foods
        ) >= model.protein_req
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs[idx] * model.quantity[idx] for idx in model.foods
        ) >= model.carbs_req
    )
    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.calories[idx] * model.quantity[idx] for idx in model.foods
        ) >= model.calories_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[idx] * model.quantity[idx] for idx in model.foods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}