import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_emp = 5
    n_proj = 5
    employees = list(range(n_emp))
    projects = list(range(n_proj))

    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_costs"]
    limits = params["assignment_limits"]

    model = pyo.ConcreteModel()

    model.emp = pyo.Set(initialize=employees)
    model.proj = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.emp, model.proj, domain=pyo.NonNegativeReals)

    model.cost = pyo.Objective(
        expr=sum(costs[i][j] * model.x[i, j] for i in employees for j in projects),
        sense=pyo.minimize,
    )

    model.avail_con = pyo.Constraint(
        model.emp,
        rule=lambda model, i: sum(model.x[i, j] for j in projects) <= availability[i],
    )

    model.req_con = pyo.Constraint(
        model.proj,
        rule=lambda model, j: sum(model.x[i, j] for i in employees) == requirements[j],
    )

    model.limit_con = pyo.Constraint(
        model.emp,
        model.proj,
        rule=lambda model, i, j: model.x[i, j] <= limits[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}