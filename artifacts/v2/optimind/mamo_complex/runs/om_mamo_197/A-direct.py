import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req_1 = params["protein_req_1"]
    protein_req_2 = params["protein_req_2"]
    calorie_req = params["calorie_req"]

    n = len(cost)

    model = pyo.ConcreteModel()

    # Structural constants may be inline; only numeric params come from dict.
    model.FOODS = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(cost[i] * m.x[i] for i in m.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein1_rule(m):
        return sum(protein[i] * m.x[i] for i in m.FOODS) >= protein_req_1

    def protein2_rule(m):
        return sum(protein[i] * m.x[i] for i in m.FOODS) >= protein_req_2

    def calorie_rule(m):
        return sum(calories[i] * m.x[i] for i in m.FOODS) >= calorie_req

    model.protein_cons_1 = pyo.Constraint(rule=protein1_rule)
    model.protein_cons_2 = pyo.Constraint(rule=protein2_rule)
    model.calorie_cons = pyo.Constraint(rule=calorie_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solver failed"}