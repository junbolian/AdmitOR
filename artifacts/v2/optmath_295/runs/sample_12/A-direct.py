import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employee_availability = params["employee_availability"]
    project_requirements = params["project_requirements"]
    assignment_cost = params["assignment_cost"]
    assignment_capacity = params["assignment_capacity"]

    num_employees = len(employee_availability)
    num_projects = len(project_requirements)

    employees = range(num_employees)
    projects = range(num_projects)

    model = pyo.ConcreteModel()

    model.employees = pyo.Set(initialize=list(employees))
    model.projects = pyo.Set(initialize=list(projects))
    model.pairs = pyo.Set(
        initialize=[(i, j) for i in employees for j in projects],
        dimen=2,
    )

    model.hours = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)

    model.cost_expr = pyo.Expression(
        expr=sum(
            assignment_cost[i][j] * model.hours[i, j] for (i, j) in model.pairs
        )
    )
    model.obj = pyo.Objective(expr=model.cost_expr, sense=pyo.minimize)

    model.emp_avail = pyo.Constraint(
        model.employees,
        rule=lambda m, i: sum(m.hours[i, j] for j in m.projects)
        <= employee_availability[i],
    )

    model.proj_req = pyo.Constraint(
        model.projects,
        rule=lambda m, j: sum(m.hours[i, j] for i in m.employees)
        == project_requirements[j],
    )

    model.cap = pyo.Constraint(
        model.pairs,
        rule=lambda m, i, j: m.hours[i, j] <= assignment_capacity[i][j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}