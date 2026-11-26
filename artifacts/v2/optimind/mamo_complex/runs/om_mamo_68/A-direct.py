import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["chicken", "rice", "tuna", "beef", "corn", "whey"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=foods)

    def protein_rule(m, f):
        return params["protein_" + f]

    def carb_rule(m, f):
        return params["carb_" + f]

    def cal_rule(m, f):
        return params["cal_" + f]

    def cost_rule(m, f):
        return params["cost_" + f]

    model.protein = pyo.Param(model.F, initialize=protein_rule)
    model.carb = pyo.Param(model.F, initialize=carb_rule)
    model.cal = pyo.Param(model.F, initialize=cal_rule)
    model.cost = pyo.Param(model.F, initialize=cost_rule)

    model.x = pyo.Var(model.F, within=pyo.NonNegativeIntegers)

    def cost_objective(m):
        return sum(m.cost[f] * m.x[f] for f in m.F)

    model.obj = pyo.Objective(rule=cost_objective, sense=pyo.minimize)

    model.protein_con = pyo.Constraint(
        expr=sum(model.protein[f] * model.x[f] for f in model.F)
        >= params["protein_target"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(model.carb[f] * model.x[f] for f in model.F)
        >= params["carb_target"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(model.cal[f] * model.x[f] for f in model.F)
        >= params["cal_target"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}