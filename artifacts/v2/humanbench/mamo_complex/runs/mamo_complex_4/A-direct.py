import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    costs = params["costs"]
    protein_content = params["protein_content"]
    carb_content = params["carb_content"]
    calorie_content = params["calorie_content"]
    protein_requirement = params["protein_requirement"]
    carb_requirement = params["carb_requirement"]
    calorie_requirement = params["calorie_requirement"]

    foods = list(range(len(costs)))

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.cost = pyo.Objective(
        expr=sum(costs[i] * model.x[i] for i in model.FOODS),
        sense=pyo.minimize,
    )

    model.protein_con = pyo.Constraint(
        expr=sum(protein_content[i] * model.x[i] for i in model.FOODS) >= protein_requirement
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb_content[i] * model.x[i] for i in model.FOODS) >= carb_requirement
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calorie_content[i] * model.x[i] for i in model.FOODS) >= calorie_requirement
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or failed: " + str(exc)}

    return {"objective": obj_val, "status": "optimal"}