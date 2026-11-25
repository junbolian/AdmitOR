import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["value"]
    salaries = params["salary"]
    budget = params["budget"]

    n = len(values)
    candidates = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(candidates, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in candidates),
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(salaries[i] * model.x[i] for i in candidates) <= budget
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}