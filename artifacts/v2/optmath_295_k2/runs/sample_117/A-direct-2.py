import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_people = 7
    n_projects = 7
    people = list(range(n_people))
    projects = list(range(n_projects))

    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    pair_cap = params["pair_cap"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(people, projects, bounds=lambda m, i, j: (0.0, float(pair_cap[i][j])))

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in people for j in projects),
        sense=pyo.minimize,
    )

    model.person_capacity = pyo.Constraint(
        people,
        rule=lambda m, i: sum(m.x[i, j] for j in projects) <= float(availability[i]),
    )

    model.project_demand = pyo.Constraint(
        projects,
        rule=lambda m, j: sum(m.x[i, j] for i in people) == float(demand[j]),
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}