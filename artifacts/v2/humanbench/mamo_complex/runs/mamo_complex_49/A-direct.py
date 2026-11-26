import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["Chicken Breast", "Tofu", "Brown Rice", "Salmon",
             "Greek Yogurt", "Steak", "Avocado", "Eggs", "Quinoa"]
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req = params["protein_req"]
    carb_req = params["carb_req"]
    calorie_req = params["calorie_req"]

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=range(len(foods)))

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(cost[i] * m.x[i] for i in m.F)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def prot_rule(m):
        return sum(protein[i] * m.x[i] for i in m.F) >= protein_req
    model.prot_con = pyo.Constraint(rule=prot_rule)

    def carb_rule(m):
        return sum(carbs[i] * m.x[i] for i in m.F) >= carb_req
    model.carb_con = pyo.Constraint(rule=carb_rule)

    def cal_rule(m):
        return sum(calories[i] * m.x[i] for i in m.F) >= calorie_req
    model.cal_con = pyo.Constraint(rule=cal_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or unsolvable: " + str(exc)}

    return {"objective": obj_val, "status": "optimal"}