import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_costs = params["assignment_costs"]
    assignment_limits = params["assignment_limits"]

    n_employees = len(employee_availability)
    n_projects = len(project_requirements)

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, n_employees - 1)
    model.projects = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.employees, model.projects, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(
            assignment_costs[i][j] * m.x[i, j]
            for i in m.employees
            for j in m.projects
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def availability_rule(m, i):
        return sum(m.x[i, j] for j in m.projects) <= employee_availability[i]

    model.availability_con = pyo.Constraint(model.employees, rule=availability_rule)

    def requirement_rule(m, j):
        return sum(m.x[i, j] for i in m.employees) == project_requirements[j]

    model.requirement_con = pyo.Constraint(model.projects, rule=requirement_rule)

    def limit_rule(m, i, j):
        return m.x[i, j] <= assignment_limits[i][j]

    model.limit_con = pyo.Constraint(model.employees, model.projects, rule=limit_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}