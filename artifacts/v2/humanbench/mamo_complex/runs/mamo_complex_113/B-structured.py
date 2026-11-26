# IR: {"sets":{"foods":"0..7"},"params":{"cost":"foods -> real","protein":"foods -> real","carbs":"foods -> real","calories":"foods -> real","req_protein":"real","req_carbs":"real","req_calories":"real"},"variables":{"quantity":{"index":"foods","type":"nonnegative continuous"}},"constraints":["sum(protein[i]*quantity[i] for i in foods) >= req_protein","sum(carbs[i]*quantity[i] for i in foods) >= req_carbs","sum(calories[i]*quantity[i] for i in foods) >= req_calories"],"objective":"minimize sum(cost[i]*quantity[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the diet LP; food inputs are sequences indexed from 0 to 7."""
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 7)

    model.cost_coeff = pyo.Param(
        model.foods,
        initialize={i: params["cost"][i] for i in model.foods},
        within=pyo.Reals,
    )
    model.protein_coeff = pyo.Param(
        model.foods,
        initialize={i: params["protein"][i] for i in model.foods},
        within=pyo.Reals,
    )
    model.carbs_coeff = pyo.Param(
        model.foods,
        initialize={i: params["carbs"][i] for i in model.foods},
        within=pyo.Reals,
    )
    model.calories_coeff = pyo.Param(
        model.foods,
        initialize={i: params["calories"][i] for i in model.foods},
        within=pyo.Reals,
    )

    model.protein_requirement = pyo.Param(
        initialize=params["req_protein"], within=pyo.Reals
    )
    model.carbs_requirement = pyo.Param(
        initialize=params["req_carbs"], within=pyo.Reals
    )
    model.calories_requirement = pyo.Param(
        initialize=params["req_calories"], within=pyo.Reals
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_coeff[i] * model.quantity[i]
            for i in model.foods
        ) >= model.protein_requirement
    )
    model.carbs_minimum = pyo.Constraint(
        expr=sum(
            model.carbs_coeff[i] * model.quantity[i]
            for i in model.foods
        ) >= model.carbs_requirement
    )
    model.calories_minimum = pyo.Constraint(
        expr=sum(
            model.calories_coeff[i] * model.quantity[i]
            for i in model.foods
        ) >= model.calories_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_coeff[i] * model.quantity[i]
            for i in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}