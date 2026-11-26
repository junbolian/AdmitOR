import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    foods = ["brownie", "ice_cream", "cola", "cheesecake"]
    
    cal = params["calories_per_food"]
    choc = params["chocolate_per_food"]
    sug = params["sugar_per_food"]
    fat = params["fat_per_food"]
    cost = params["cost_per_food"]
    
    min_cal = params["min_calories"]
    min_choc = params["min_chocolate"]
    min_sug = params["min_sugar"]
    min_fat = params["min_fat"]
    
    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)
    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)
    
    model.cost_expr = pyo.Objective(
        expr=sum(cost[i] * model.x[f] for i, f in enumerate(foods)),
        sense=pyo.minimize,
    )
    
    model.cal_con = pyo.Constraint(
        expr=sum(cal[i] * model.x[f] for i, f in enumerate(foods)) >= min_cal
    )
    model.choc_con = pyo.Constraint(
        expr=sum(choc[i] * model.x[f] for i, f in enumerate(foods)) >= min_choc
    )
    model.sug_con = pyo.Constraint(
        expr=sum(sug[i] * model.x[f] for i, f in enumerate(foods)) >= min_sug
    )
    model.fat_con = pyo.Constraint(
        expr=sum(fat[i] * model.x[f] for i, f in enumerate(foods)) >= min_fat
    )
    
    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_expr))
    return {"objective": obj_val, "status": "optimal"}