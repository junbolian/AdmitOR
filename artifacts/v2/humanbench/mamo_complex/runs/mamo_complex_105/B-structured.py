# IR: {"sets":{"foods":[0,1,2,3,4]},"params":{"cost":"five-element sequence indexed by foods","protein":"five-element sequence indexed by foods","carbs":"five-element sequence indexed by foods","calories":"five-element sequence indexed by foods","protein_req":"scalar","carbs_req":"scalar","calories_req":"scalar"},"variables":{"quantity[foods]":"NonNegativeReals"},"constraints":["sum(protein[i]*quantity[i] for i in foods) >= protein_req","sum(carbs[i]*quantity[i] for i in foods) >= carbs_req","sum(calories[i]*quantity[i] for i in foods) >= calories_req"],"objective":"minimize sum(cost[i]*quantity[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Inputs use zero-based sequences: index 0 corresponds to Food_1."""
    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=range(5), ordered=True)

    model.cost = pyo.Param(
        model.foods,
        initialize={idx: params["cost"][idx] for idx in model.foods},
        within=pyo.Reals,
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={idx: params["protein"][idx] for idx in model.foods},
        within=pyo.Reals,
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={idx: params["carbs"][idx] for idx in model.foods},
        within=pyo.Reals,
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={idx: params["calories"][idx] for idx in model.foods},
        within=pyo.Reals,
    )
    model.protein_req = pyo.Param(
        initialize=params["protein_req"], within=pyo.Reals
    )
    model.carbs_req = pyo.Param(
        initialize=params["carbs_req"], within=pyo.Reals
    )
    model.calories_req = pyo.Param(
        initialize=params["calories_req"], within=pyo.Reals
    )

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
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}