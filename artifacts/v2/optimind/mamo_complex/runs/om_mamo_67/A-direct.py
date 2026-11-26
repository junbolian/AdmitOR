import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken", "Pasta", "Rice", "Beans", "Cheese"]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeIntegers)

    model.protein = pyo.Param(model.F, initialize={f: params["protein_" + f] for f in foods})
    model.carbs = pyo.Param(model.F, initialize={f: params["carbs_" + f] for f in foods})
    model.calories = pyo.Param(model.F, initialize={f: params["calories_" + f] for f in foods})
    model.cost = pyo.Param(model.F, initialize={f: params["cost_" + f] for f in foods})

    model.protein_con = pyo.Constraint(
        expr=sum(model.protein[f] * model.x[f] for f in model.F) >= params["protein_requirement"]
    )
    model.carbs_con = pyo.Constraint(
        expr=sum(model.carbs[f] * model.x[f] for f in model.F) >= params["carbs_requirement"]
    )
    model.calories_con = pyo.Constraint(
        expr=sum(model.calories[f] * model.x[f] for f in model.F) >= params["calories_requirement"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[f] * model.x[f] for f in model.F),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}