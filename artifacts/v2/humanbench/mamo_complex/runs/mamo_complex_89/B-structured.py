# IR: {"sets":{"foods":"0..8 in the listed food order"},"params":{"cost":"cost[i]","protein":"protein[i]","carbs":"carbs[i]","calories":"calories[i]","protein_req":"minimum protein","carb_req":"minimum carbohydrates","calorie_req":"minimum calories"},"variables":{"quantity[i]":"NonNegativeReals"},"constraints":["sum(protein[i]*quantity[i]) >= protein_req","sum(carbs[i]*quantity[i]) >= carb_req","sum(calories[i]*quantity[i]) >= calorie_req"],"objective":"minimize sum(cost[i]*quantity[i])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Nutrient and cost inputs use indices 0 through 8 in food order."""
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 8)

    model.cost = pyo.Param(
        model.foods, initialize={i: params["cost"][i] for i in model.foods}
    )
    model.protein = pyo.Param(
        model.foods, initialize={i: params["protein"][i] for i in model.foods}
    )
    model.carbs = pyo.Param(
        model.foods, initialize={i: params["carbs"][i] for i in model.foods}
    )
    model.calories = pyo.Param(
        model.foods, initialize={i: params["calories"][i] for i in model.foods}
    )
    model.protein_req = pyo.Param(initialize=params["protein_req"])
    model.carb_req = pyo.Param(initialize=params["carb_req"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(model.protein[i] * model.quantity[i] for i in model.foods)
        >= model.protein_req
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(model.carbs[i] * model.quantity[i] for i in model.foods)
        >= model.carb_req
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(model.calories[i] * model.quantity[i] for i in model.foods)
        >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i] * model.quantity[i] for i in model.foods),
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