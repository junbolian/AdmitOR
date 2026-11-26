import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    candidates = ['F', 'G', 'H', 'I', 'J']

    salary = {c: params["salary_" + c] for c in candidates}
    skill = {c: params["skill_" + c] for c in candidates}
    exp = {c: params["exp_" + c] for c in candidates}

    model.x = pyo.Var(candidates, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(salary[c] * model.x[c] for c in candidates),
        sense=pyo.minimize
    )

    model.budget_con = pyo.Constraint(
        expr=sum(salary[c] * model.x[c] for c in candidates) <= params["budget"]
    )
    model.max_hires_con = pyo.Constraint(
        expr=sum(model.x[c] for c in candidates) <= params["max_hires"]
    )
    model.skill_con = pyo.Constraint(
        expr=sum(skill[c] * model.x[c] for c in candidates) >= params["min_skill"]
    )
    model.exp_con = pyo.Constraint(
        expr=sum(exp[c] * model.x[c] for c in candidates) >= params["min_exp"]
    )
    model.gj_con = pyo.Constraint(
        expr=model.x['G'] + model.x['J'] <= 1
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}