import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    cost_matrix = params["cost_matrix"]
    assignment_capacity = params["assignment_capacity"]

    n_consultants = len(consultant_availability)
    n_projects = len(project_requirements)

    consultants = list(range(n_consultants))
    projects = list(range(n_projects))
    pairs = [(i, j) for i in consultants for j in projects]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j] for (i, j) in pairs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def project_rule(m, j):
        return sum(m.x[i, j] for i in consultants) >= project_requirements[j]

    model.project_req = pyo.Constraint(projects, rule=project_rule)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in projects) <= consultant_availability[i]

    model.avail = pyo.Constraint(consultants, rule=avail_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= assignment_capacity[i][j]

    model.cap = pyo.Constraint(pairs, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}