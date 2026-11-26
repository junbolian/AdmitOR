import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Steak", "Rice", "Chicken", "Iceberg Lettuce", "Almonds"]
    n = len(foods)

    protein = [params["protein_content"][i] for i in range(n)]
    carb = [params["carb_content"][i] for i in range(n)]
    calorie = [params["calorie_content"][i] for i in range(n)]
    cost = [params["cost"][i] for i in range(n)]

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, n - 1)
    model.x = pyo.Var(model.F, domain=pyo.NonNegativeIntegers)

    model.protein_req = params["protein_requirement"]
    model.carb_req = params["carb_requirement"]
    model.calorie_req = params["calorie_requirement"]

    model.protein_con = pyo.Constraint(
        expr=sum(protein[i] * model.x[i] for i in model.F) >= model.protein_req
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[i] * model.x[i] for i in model.F) >= model.carb_req
    )
    model.calorie_con = pyo.Constraint(
        expr=sum(calorie[i] * model.x[i] for i in model.F) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.x[i] for i in model.F), sense=pyo.minimize
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}