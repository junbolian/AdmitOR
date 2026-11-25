import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    consultant_availability = params["consultant_availability"]
    project_requirements = params["project_requirements"]
    cost_matrix = params["cost_matrix"]
    assignment_capacity = params["assignment_capacity"]

    n_consultants = len(consultant_availability)
    n_projects = len(project_requirements)

    model = pyo.ConcreteModel()

    model.consultants = pyo.RangeSet(0, n_consultants - 1)
    model.projects = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.consultants, model.projects, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost_matrix[i][j] * m.x[i, j]
                   for i in m.consultants for j in m.projects)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def project_rule(m, j):
        return sum(m.x[i, j] for i in m.consultants) >= project_requirements[j]

    model.project_demand = pyo.Constraint(model.projects, rule=project_rule)

    def avail_rule(m, i):
        return sum(m.x[i, j] for j in m.projects) <= consultant_availability[i]

    model.consultant_avail = pyo.Constraint(model.consultants, rule=avail_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= assignment_capacity[i][j]

    model.assignment_cap = pyo.Constraint(model.consultants, model.projects, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}