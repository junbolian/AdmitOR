# IR: {"sets":{"employees":[0,1,2,3,4,5],"projects":[0,1,2,3,4,5]},"params":{"employee_availability":"nonnegative vector indexed by employee","project_requirement":"nonnegative vector indexed by project","assignment_cost":"real matrix indexed by employee, project","per_assignment_capacity":"nonnegative matrix indexed by employee, project"},"variables":{"hours[i,j]":"continuous nonnegative"},"constraints":["sum_j hours[i,j] == employee_availability[i] for each employee i","sum_i hours[i,j] == project_requirement[j] for each project j","hours[i,j] <= per_assignment_capacity[i,j] for each employee i and project j"],"objective":"minimize sum_i sum_j assignment_cost[i,j] * hours[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the assignment LP using indexable vectors and nested matrices."""
    employee_availability = params["employee_availability"]
    project_requirement = params["project_requirement"]
    assignment_cost = params["assignment_cost"]
    per_assignment_capacity = params["per_assignment_capacity"]

    model = pyo.ConcreteModel()

    model.employees = pyo.RangeSet(0, 5)
    model.projects = pyo.RangeSet(0, 5)

    model.employee_availability = pyo.Param(
        model.employees,
        initialize=lambda mdl, i: employee_availability[i],
        within=pyo.NonNegativeReals,
    )
    model.project_requirement = pyo.Param(
        model.projects,
        initialize=lambda mdl, j: project_requirement[j],
        within=pyo.NonNegativeReals,
    )
    model.assignment_cost = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: assignment_cost[i][j],
        within=pyo.Reals,
    )
    model.per_assignment_capacity = pyo.Param(
        model.employees,
        model.projects,
        initialize=lambda mdl, i, j: per_assignment_capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.employees,
        model.projects,
        domain=pyo.NonNegativeReals,
    )

    model.employee_balance = pyo.Constraint(
        model.employees,
        rule=lambda mdl, i: (
            sum(mdl.hours[i, j] for j in mdl.projects)
            == mdl.employee_availability[i]
        ),
    )
    model.project_balance = pyo.Constraint(
        model.projects,
        rule=lambda mdl, j: (
            sum(mdl.hours[i, j] for i in mdl.employees)
            == mdl.project_requirement[j]
        ),
    )
    model.assignment_limit = pyo.Constraint(
        model.employees,
        model.projects,
        rule=lambda mdl, i, j: (
            mdl.hours[i, j] <= mdl.per_assignment_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.assignment_cost[i, j] * model.hours[i, j]
            for i in model.employees
            for j in model.projects
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}