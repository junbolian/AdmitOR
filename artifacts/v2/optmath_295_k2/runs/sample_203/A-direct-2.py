import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_consultants = len(consultant_hours)
    n_projects = len(project_hours)

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, n_consultants - 1)
    model.P = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.C, model.P, domain=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, capacity[i][j]))

    model.cons_consultant = pyo.Constraint(
        model.C,
        rule=lambda m, i: sum(m.x[i, j] for j in m.P) == consultant_hours[i],
    )

    model.cons_project = pyo.Constraint(
        model.P,
        rule=lambda m, j: sum(m.x[i, j] for i in m.C) == project_hours[j],
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.C for j in model.P),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}