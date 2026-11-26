import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "apples", "cheese", "tofu"]

    model = pyo.ConcreteModel()
    model.FOODS = pyo.Set(initialize=foods)

    model.protein = pyo.Param(model.FOODS, initialize={
        f: params["protein_" + f] for f in foods})
    model.carb = pyo.Param(model.FOODS, initialize={
        f: params["carb_" + f] for f in foods})
    model.cal = pyo.Param(model.FOODS, initialize={
        f: params["cal_" + f] for f in foods})
    model.cost = pyo.Param(model.FOODS, initialize={
        f: params["cost_" + f] for f in foods})

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[f] * model.x[f] for f in model.FOODS),
        sense=pyo.minimize)

    model.protein_con = pyo.Constraint(
        expr=sum(model.protein[f] * model.x[f] for f in model.FOODS)
        >= params["protein_req"])
    model.carb_con = pyo.Constraint(
        expr=sum(model.carb[f] * model.x[f] for f in model.FOODS)
        >= params["carb_req"])
    model.cal_con = pyo.Constraint(
        expr=sum(model.cal[f] * model.x[f] for f in model.FOODS)
        >= params["cal_req"])

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}