import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    capacity_limits = params["capacity_limits"]

    n_emp = len(employee_availability)
    n_proj = len(project_requirements)

    employees = list(range(n_emp))
    projects = list(range(n_proj))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=employees)
    model.J = pyo.Set(initialize=projects)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(assignment_costs[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def employee_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == employee_availability[i]

    model.employee_con = pyo.Constraint(model.I, rule=employee_rule)

    def project_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == project_requirements[j]

    model.project_con = pyo.Constraint(model.J, rule=project_rule)

    def capacity_rule(m, i, j):
        return m.x[i, j] <= capacity_limits[i][j]

    model.capacity_con = pyo.Constraint(model.I, model.J, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}