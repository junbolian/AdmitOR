import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    employee_capacity = params["employee_capacity"]
    project_demand = params["project_demand"]
    per_project_limit = params["per_project_limit"]

    employees = list(range(len(employee_capacity)))
    projects = list(range(len(project_demand)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(employees, projects, domain=pyo.NonNegativeReals)

    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in employees for j in projects),
        sense=pyo.minimize,
    )

    model.emp_cap = pyo.Constraint(
        employees,
        rule=lambda model, i: sum(model.x[i, j] for j in projects) == employee_capacity[i],
    )
    model.proj_dem = pyo.Constraint(
        projects,
        rule=lambda model, j: sum(model.x[i, j] for i in employees) == project_demand[j],
    )
    model.limit = pyo.Constraint(
        employees,
        projects,
        rule=lambda model, i, j: model.x[i, j] <= per_project_limit[i][j],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}