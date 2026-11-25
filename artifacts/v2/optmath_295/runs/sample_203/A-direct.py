import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_hours = params["consultant_hours"]
    project_hours = params["project_hours"]
    capacity = params["capacity"]
    cost = params["cost"]

    n_consultants = len(consultant_hours)
    n_projects = len(project_hours)
    consultants = list(range(n_consultants))
    projects = list(range(n_projects))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=consultants)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.I for j in model.J),
        sense=pyo.minimize,
    )

    model.consultant_hours_con = pyo.Constraint(
        model.I,
        rule=lambda m, i: sum(m.x[i, j] for j in m.J) == consultant_hours[i],
    )

    model.project_hours_con = pyo.Constraint(
        model.J,
        rule=lambda m, j: sum(m.x[i, j] for i in m.I) == project_hours[j],
    )

    model.capacity_con = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda m, i, j: m.x[i, j] <= capacity[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}