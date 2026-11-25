import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    per_project_limit = params["per_project_limit"]

    num_people = len(availability)
    num_projects = len(project_requirement)

    people = list(range(num_people))
    projects = list(range(num_projects))

    model = pyo.ConcreteModel()

    model.person_set = pyo.Set(initialize=people)
    model.project_set = pyo.Set(initialize=projects)

    model.hours = pyo.Var(
        model.person_set,
        model.project_set,
        domain=pyo.NonNegativeReals,
    )

    def objective_rule(m):
        return sum(
            assignment_cost[i][j] * m.hours[i, j]
            for i in people
            for j in projects
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def availability_rule(m, i):
        return sum(m.hours[i, j] for j in projects) <= availability[i]

    model.availability_con = pyo.Constraint(model.person_set, rule=availability_rule)

    def requirement_rule(m, j):
        return sum(m.hours[i, j] for i in people) == project_requirement[j]

    model.requirement_con = pyo.Constraint(model.project_set, rule=requirement_rule)

    def limit_rule(m, i, j):
        return m.hours[i, j] <= per_project_limit[i][j]

    model.limit_con = pyo.Constraint(
        model.person_set, model.project_set, rule=limit_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}