import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    candidates = ['A', 'B', 'C', 'D', 'E']

    model = pyo.ConcreteModel()

    model.x = pyo.Var(candidates, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(params["salary_" + c] * model.x[c] for c in candidates),
        sense=pyo.minimize,
    )

    model.max_hires_con = pyo.Constraint(
        expr=sum(model.x[c] for c in candidates) <= params["max_hires"]
    )

    model.min_hires_con = pyo.Constraint(
        expr=sum(model.x[c] for c in candidates) >= params["min_hires"]
    )

    model.budget_con = pyo.Constraint(
        expr=sum(params["salary_" + c] * model.x[c] for c in candidates)
        <= params["budget"]
    )

    model.experience_con = pyo.Constraint(
        expr=sum(params["experience_" + c] * model.x[c] for c in candidates)
        >= params["min_experience"]
    )

    model.pair_ae_con = pyo.Constraint(
        expr=model.x['A'] + model.x['E'] <= params["max_from_A_E"]
    )

    advanced = ['B', 'C']
    model.advanced_degree_con = pyo.Constraint(
        expr=sum(model.x[c] for c in advanced) >= params["min_advanced_degree"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {'objective': obj_val, 'status': 'optimal'}