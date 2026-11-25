import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_hours = params["employee_hours"]
    project_hours = params["project_hours"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_emp = len(employee_hours)
    n_proj = len(project_hours)
    employees = range(n_emp)
    projects = range(n_proj)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(employees, projects, domain=pyo.NonNegativeReals)

    def cost_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in employees for j in projects)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    model.emp_balance = pyo.Constraint(
        employees,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in projects) == employee_hours[i],
    )

    model.proj_balance = pyo.Constraint(
        projects,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in employees) == project_hours[j],
    )

    model.cap_limit = pyo.Constraint(
        employees,
        projects,
        rule=lambda mdl, i, j: mdl.x[i, j] <= capacity[i][j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}