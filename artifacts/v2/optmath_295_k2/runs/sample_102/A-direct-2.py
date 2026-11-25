import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["employee_availability"]
    requirements = params["project_requirements"]
    costs = params["assignment_costs"]
    limits = params["assignment_limits"]

    n_emp = len(availability)
    n_proj = len(requirements)
    employees = range(n_emp)
    projects = range(n_proj)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(employees, projects, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(costs[i][j] * m.x[i, j] for i in employees for j in projects)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    model.emp_limit = pyo.Constraint(
        employees,
        rule=lambda m, i: sum(m.x[i, j] for j in projects) <= availability[i],
    )

    model.proj_req = pyo.Constraint(
        projects,
        rule=lambda m, j: sum(m.x[i, j] for i in employees) == requirements[j],
    )

    def proj_limit_rule(m, i, j):
        return m.x[i, j] <= limits[i][j]

    model.proj_limit = pyo.Constraint(employees, projects, rule=proj_limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}