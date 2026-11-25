import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    requirements = params["requirements"]
    cost = params["cost"]
    limit = params["limit"]

    n_people = len(availability)
    n_projects = len(requirements)
    people = range(n_people)
    projects = range(n_projects)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(people, projects, domain=pyo.NonNegativeReals, bounds=(0, None))

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in people for j in projects),
        sense=pyo.minimize,
    )

    model.person_avail = pyo.Constraint(
        people,
        rule=lambda m, i: sum(m.x[i, j] for j in projects) <= availability[i],
    )

    model.project_req = pyo.Constraint(
        projects,
        rule=lambda m, j: sum(m.x[i, j] for i in people) == requirements[j],
    )

    model.per_limit = pyo.Constraint(
        people, projects,
        rule=lambda m, i, j: m.x[i, j] <= limit[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}