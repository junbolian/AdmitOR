import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    assignment_limit = params["assignment_limit"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirement)

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, num_employees - 1)
    model.projects = pyo.RangeSet(0, num_projects - 1)

    model.hours = pyo.Var(
        model.employees, model.projects, domain=pyo.NonNegativeReals
    )

    def cost_rule(m):
        return sum(
            assignment_cost[i][j] * m.hours[i, j]
            for i in m.employees
            for j in m.projects
        )

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def availability_rule(m, i):
        return (
            sum(m.hours[i, j] for j in m.projects) <= employee_availability[i]
        )

    model.availability_con = pyo.Constraint(model.employees, rule=availability_rule)

    def requirement_rule(m, j):
        return sum(m.hours[i, j] for i in m.employees) == project_requirement[j]

    model.requirement_con = pyo.Constraint(model.projects, rule=requirement_rule)

    def limit_rule(m, i, j):
        return m.hours[i, j] <= assignment_limit[i][j]

    model.limit_con = pyo.Constraint(
        model.employees, model.projects, rule=limit_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}