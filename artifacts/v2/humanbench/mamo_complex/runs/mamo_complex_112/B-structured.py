# IR: {"sets":{"foods":[0,1,2,3,4,5]},"params":{"cost":"six values indexed 0..5","protein":"six values indexed 0..5","carbs":"six values indexed 0..5; informational only","calories":"six values indexed 0..5","req_protein_1":"scalar","req_protein_2":"scalar","req_calories":"scalar"},"variables":{"quantity[i]":"nonnegative continuous, i in foods"},"constraints":["sum(protein[i]*quantity[i]) >= req_protein_1","sum(protein[i]*quantity[i]) >= req_protein_2","sum(calories[i]*quantity[i]) >= req_calories"],"objective":"minimize sum(cost[i]*quantity[i])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept six-item sequences or mappings indexed 0 through 5.

    Both stated protein requirements are enforced as minimums.
    No carbohydrate requirement is specified.
    """
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 5)

    model.cost = pyo.Param(
        model.foods,
        initialize={idx: params["cost"][idx] for idx in model.foods},
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={idx: params["protein"][idx] for idx in model.foods},
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={idx: params["carbs"][idx] for idx in model.foods},
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={idx: params["calories"][idx] for idx in model.foods},
    )
    model.req_protein_1 = pyo.Param(initialize=params["req_protein_1"])
    model.req_protein_2 = pyo.Param(initialize=params["req_protein_2"])
    model.req_calories = pyo.Param(initialize=params["req_calories"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement_1 = pyo.Constraint(
        expr=sum(
            model.protein[idx] * model.quantity[idx] for idx in model.foods
        ) >= model.req_protein_1
    )
    model.protein_requirement_2 = pyo.Constraint(
        expr=sum(
            model.protein[idx] * model.quantity[idx] for idx in model.foods
        ) >= model.req_protein_2
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.calories[idx] * model.quantity[idx] for idx in model.foods
        ) >= model.req_calories
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